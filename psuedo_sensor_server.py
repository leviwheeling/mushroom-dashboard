import asyncio
import json
from datetime import datetime
import websockets

# Attempt to import from sensor_handler
try:
    from sensor_handler import ZONE_NAMES, generate_pseudo_sensor_data
    SENSOR_HANDLER_AVAILABLE = True
except ImportError:
    print("Warning: sensor_handler.py not found or incomplete. Using placeholder data.")
    # Define placeholders if import fails, so the server can at least start and show the error.
    ZONE_NAMES = ["Default Zone (Import Error)"]
    def generate_pseudo_sensor_data(base_time=None, zone_name=None):
        return {
            "timestamp": (base_time or datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": 0, "humidity": 0, "CO2": 0, "zone": zone_name or "ErrorZone",
            "error": "Failed to import from sensor_handler.py"
        }
    SENSOR_HANDLER_AVAILABLE = False # Explicitly set to False

# Set the WebSocket port (adjust if needed)
PORT = 8765

# Removed local generate_pseudo_sensor_data function as it's now imported

async def sensor_data_handler(websocket, path):
    """
    Continuously send pseudo sensor data for all zones over the WebSocket connection every 5 seconds.
    """
    print(f"Client connected: {websocket.remote_address}")
    try:
        while True:
            all_zone_data = []
            current_time = datetime.now() # Use the same base time for all zones in a single batch

            for zone_name in ZONE_NAMES:
                # Call the imported generate_pseudo_sensor_data from sensor_handler
                data_point = generate_pseudo_sensor_data(base_time=current_time, zone_name=zone_name)
                all_zone_data.append(data_point)
            
            if all_zone_data:
                # Updated print statement
                # Check if temperature exists and is a number before formatting
                temp_sample = all_zone_data[0].get('temperature', 'N/A')
                if isinstance(temp_sample, (int, float)):
                    temp_display = f"{temp_sample:.1f}°F"
                else:
                    temp_display = str(temp_sample) # Display as is if not a number

                print(f"Sending data for {len(all_zone_data)} zones. (Sample: {all_zone_data[0]['zone']} - {temp_display})")
                await websocket.send(json.dumps(all_zone_data))
            else:
                # This case should ideally not be reached if ZONE_NAMES is properly populated (even by fallback)
                print("Warning: No zone data generated to send. ZONE_NAMES might be empty.") 
                # Send an empty array to potentially satisfy client expecting JSON array
                await websocket.send(json.dumps([])) 
                
            await asyncio.sleep(5) # Send a batch of readings for all zones every 5 seconds
            
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client {websocket.remote_address} disconnected normally.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Client {websocket.remote_address} disconnected with error: {e}")
    except Exception as e:
        # Catching other potential errors during the loop or sending
        print(f"Error in sensor_data_handler for client {websocket.remote_address}: {e}")
    finally:
        # Ensure this print statement is consistent for all disconnections
        print(f"Client {websocket.remote_address} session ended.")

async def main():
    # Start the WebSocket server
    server = await websockets.serve(sensor_data_handler, "0.0.0.0", PORT)
    print(f"Pseudo Sensor WebSocket Server running on ws://0.0.0.0:{PORT}")
    
    if SENSOR_HANDLER_AVAILABLE:
        print(f"Broadcasting data for zones: {', '.join(ZONE_NAMES)}")
    else:
        print("CRITICAL WARNING: sensor_handler.py could not be imported. Server is running with placeholder data and functionality will be incorrect.")
        print(f"Broadcasting placeholder data for zone(s): {', '.join(ZONE_NAMES)}")
    
    # Keep the server running until it's stopped (e.g., by Ctrl+C)
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully...")
    except Exception as e:
        print(f"Failed to start server: {e}")
        if "sensor_handler.py not found" in str(e) or isinstance(e, ImportError):
             print("Please ensure sensor_handler.py is in the same directory as psuedo_sensor_server.py")
