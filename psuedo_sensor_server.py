import asyncio
import json
import random
from datetime import datetime

import websockets

# Set the WebSocket port (adjust if needed)
PORT = 8765

def generate_pseudo_sensor_data():
    """
    Generate pseudo sensor data with the same keys as the Excel-based data.
    - timestamp: current time in the format "YYYY-MM-DD HH:MM:SS"
    - temperature: random float between 40°F and 50°F
    - humidity: random float between 95% and 100%
    - CO2: random integer between 440 and 500 ppm
    """
    now = datetime.now()
    sensor_data = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": round(random.uniform(40.0, 50.0), 2),
        "humidity": round(random.uniform(95.0, 100.0), 2),
        "CO2": random.randint(440, 500)
    }
    return sensor_data

async def sensor_data_handler(websocket, path):
    """
    Continuously send pseudo sensor data over the WebSocket connection every 5 seconds.
    """
    print("Client connected:", websocket.remote_address)
    try:
        while True:
            data = generate_pseudo_sensor_data()
            print("Sending pseudo data:", data)
            await websocket.send(json.dumps(data))
            await asyncio.sleep(5)
    except Exception as e:
        print("Error:", e)
    finally:
        print("Client disconnected:", websocket.remote_address)

async def main():
    async with websockets.serve(sensor_data_handler, "0.0.0.0", PORT):
        print(f"Pseudo Sensor WebSocket Server running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())