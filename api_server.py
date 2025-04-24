import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from sensor_handler import read_sensor_data
from ai_model import start_conversation, send_message
from insight_bot import get_insight

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all origins.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def numpy_encoder(o):
    try:
        return int(o)
    except Exception:
        return o

# Global variable to hold the latest insight JSON.
INSIGHT_MSG = {"historicalSummary": "", "currentReading": "", "insight": "No insight available yet."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            sensor_data, _ = read_sensor_data()
            if sensor_data:
                await websocket.send_text(json.dumps(sensor_data, default=numpy_encoder))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print("Client disconnected from sensor data WebSocket")

@app.post("/chat")
async def chat_endpoint(request: Request):
    payload = await request.json()
    user_message = payload.get("message")
    if not user_message:
        return {"error": "Message is required."}
    sensor_context = (
        f"Sensor Data Context: Current reading - Temperature: {read_sensor_data()[0]['temperature']}°F, "
        f"Humidity: {read_sensor_data()[0]['humidity']}%, CO2: {read_sensor_data()[0]['CO2']} ppm. "
        f"Historical data includes {len(read_sensor_data()[1])} readings. "
        "Ignore the sensor data when generating your response, but keep it in consideration for overall trends."
    )
    full_message = f"{sensor_context}\nUser: {user_message}"
    thread_id = payload.get("thread_id")
    if not thread_id:
        thread_id = start_conversation()
    ai_reply = send_message(thread_id, full_message)
    return {"thread_id": thread_id, "reply": ai_reply}

@app.get("/history")
async def get_history():
    _, history_data = read_sensor_data()
    if history_data:
        return history_data
    return []

@app.get("/insight")
async def insight_endpoint():
    return {"insight": INSIGHT_MSG}

@app.get("/run_insight")
async def run_insight_endpoint():
    new_insight = await asyncio.to_thread(get_insight)
    global INSIGHT_MSG
    INSIGHT_MSG = new_insight
    return {"insight": new_insight}

async def update_insight_periodically():
    global INSIGHT_MSG
    while True:
        new_insight = await asyncio.to_thread(get_insight)
        INSIGHT_MSG = new_insight
        await asyncio.sleep(600)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_insight_periodically())

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)