import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import websockets # For relaying

# Attempt to import project-specific modules
try:
    from sensor_handler import read_sensor_data, ZONE_NAMES
    from ai_model import start_conversation as start_ai_conversation, send_message as send_ai_message
    from insight_bot import get_insight
    MODULES_LOADED = True
except ImportError as e:
    print(f"Warning: Failed to import one or more project modules: {e}. API might not function fully.")
    MODULES_LOADED = False
    # Define fallbacks if modules are not loaded, to allow server to start
    ZONE_NAMES = ["DefaultZoneOnError"] 
    def read_sensor_data(zone_name): return ({"error": "sensor_handler not loaded"}, [])
    def start_ai_conversation(): return "dummy_thread_id_error"
    def send_ai_message(thread_id, msg, zone): return "AI model not loaded"
    def get_insight(zone): return {"error": "insight_bot not loaded"}


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PSEUDO_SERVER_URI = "ws://localhost:8765"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "Unknown"
    client_port = websocket.client.port if websocket.client else "N/A"
    client_id = f"{client_host}:{client_port}"
    print(f"Client {client_id} connected to /ws relay.")
    
    upstream_websocket = None # Define to ensure it's available in finally block
    try:
        async with websockets.connect(PSEUDO_SERVER_URI) as ws_upstream:
            upstream_websocket = ws_upstream # Assign to outer scope variable for finally block
            print(f"Successfully connected to upstream pseudo_sensor_server at {PSEUDO_SERVER_URI} for client {client_id}")
            try:
                while True:
                    # Listen to both websockets concurrently
                    upstream_task = asyncio.create_task(upstream_websocket.recv())
                    client_task = asyncio.create_task(websocket.receive_text()) # Check for client disconnects/messages

                    done, pending = await asyncio.wait(
                        [upstream_task, client_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    if client_task in done:
                        try:
                            client_message = client_task.result()
                            # Optional: Process client_message if your protocol defines client-to-server messages for /ws
                            # print(f"Received from client {client_id}: {client_message}")
                        except WebSocketDisconnect:
                            print(f"Client {client_id} disconnected (handled by client_task).")
                            for task in pending: task.cancel() # Cancel pending upstream recv
                            break 
                        except Exception as e_client_recv:
                            print(f"Error receiving from client {client_id}: {e_client_recv}")
                            for task in pending: task.cancel()
                            break

                    if upstream_task in done:
                        try:
                            message = upstream_task.result()
                            await websocket.send_text(message)
                        except websockets.exceptions.ConnectionClosed:
                            print(f"Upstream pseudo_sensor_server connection closed for client {client_id}.")
                            await websocket.send_text(json.dumps({"error": "Live sensor data feed disconnected."}))
                            for task in pending: task.cancel() # Cancel pending client recv
                            break 
                        except Exception as e_upstream_recv:
                            print(f"Error from upstream or sending to client {client_id}: {e_upstream_recv}")
                            await websocket.send_text(json.dumps({"error": f"Error in data relay: {str(e_upstream_recv)}"}))
                            for task in pending: task.cancel()
                            break
                    
                    # Ensure all pending tasks are cancelled if one completed, to restart loop cleanly
                    for task in pending:
                        task.cancel()

            except WebSocketDisconnect: 
                print(f"Client {client_id} disconnected (WebSocketDisconnect exception).")
            except websockets.exceptions.ConnectionClosed as e: 
                print(f"Upstream pseudo_sensor_server connection closed unexpectedly for client {client_id}: {e}")
                try:
                    await websocket.send_text(json.dumps({"error": "Live sensor data feed connection lost."}))
                except: pass 
            except Exception as e_loop:
                print(f"Error in relay loop for client {client_id}: {e_loop}")
                try:
                    await websocket.send_text(json.dumps({"error": f"Error in live data feed: {str(e_loop)}"}))
                except: pass

    except (websockets.exceptions.ConnectionClosedOSError, ConnectionRefusedError) as e: 
        print(f"Could not connect to upstream pseudo_sensor_server at {PSEUDO_SERVER_URI} for client {client_id}: {e}. Is it running?")
        try:
            await websocket.send_text(json.dumps({"error": "Cannot connect to live sensor data feed. Upstream server offline."}))
        except: pass
    except Exception as e_connect:
        print(f"Overall error in /ws endpoint for client {client_id} during connection phase: {e_connect}")
        try:
            await websocket.send_text(json.dumps({"error": f"A server error occurred in the live data feed setup: {str(e_connect)}"}))
        except: pass
    finally:
        print(f"Client {client_id} session ended for /ws relay.")
        if upstream_websocket and not upstream_websocket.closed:
            await upstream_websocket.close()
            print(f"Closed connection to upstream for client {client_id}")
        # FastAPI typically handles closing the `websocket` (client-facing) connection.


@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
        
    user_message = payload.get("message")
    thread_id = payload.get("thread_id")
    zone_name = payload.get("zone_name") 

    if not user_message:
        raise HTTPException(status_code=422, detail="Message ('message') is required in the JSON body.")
    if not zone_name:
        raise HTTPException(status_code=422, detail="Zone name ('zone_name') is required in the JSON body.")
    if zone_name not in ZONE_NAMES: # Make sure ZONE_NAMES is available in this scope
        raise HTTPException(status_code=422, detail=f"Invalid zone_name: '{zone_name}'. Must be one of {ZONE_NAMES}.")

    if not thread_id:
        thread_id = start_ai_conversation() 

    try:
        ai_reply = send_ai_message(thread_id, user_message, zone_name)
        return {"thread_id": thread_id, "reply": ai_reply, "zone_name": zone_name}
    except Exception as e:
        print(f"Error in /chat calling send_ai_message: {e}")
        raise HTTPException(status_code=500, detail=f"AI interaction failed: {str(e)}")


@app.get("/history")
async def get_history(zone_name: str): 
    if zone_name not in ZONE_NAMES:
        raise HTTPException(status_code=404, detail=f"Invalid zone_name: '{zone_name}'. Must be one of {ZONE_NAMES}.")
    try:
        latest_data, history_data = read_sensor_data(zone_name=zone_name)
        return {"latest": latest_data, "history": history_data}
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in /history for zone {zone_name}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected server error occurred.")

@app.get("/run_insight")
async def run_insight_endpoint(zone_name: str): 
    if zone_name not in ZONE_NAMES:
        raise HTTPException(status_code=404, detail=f"Invalid zone_name: '{zone_name}'. Must be one of {ZONE_NAMES}.")
    try:
        new_insight = await asyncio.to_thread(get_insight, zone_name)
        if isinstance(new_insight, dict) and new_insight.get("error"): 
             raise HTTPException(status_code=500, detail=new_insight.get("error"))
        return {"zone_name": zone_name, "insight": new_insight}
    except Exception as e:
        print(f"Error in /run_insight for zone {zone_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")

@app.on_event("startup")
async def startup_event():
    print("FastAPI server startup complete.")
    print("Note: Periodic insight update is currently disabled.")
    print(f"Live sensor data will be relayed from: {PSEUDO_SERVER_URI}")
    # Ensure ZONE_NAMES is loaded and available for validation if needed at startup
    if not MODULES_LOADED: # Check the flag set during initial imports
        print("CRITICAL WARNING: Some project modules (sensor_handler, ai_model, insight_bot) may not have loaded correctly. API functionality will be severely limited.")
    elif not ZONE_NAMES or ZONE_NAMES == ["DefaultZoneOnError"]: # Check specific fallback for ZONE_NAMES
        print("Warning: ZONE_NAMES could not be loaded correctly from sensor_handler. Zone validation might fail or use default.")


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
