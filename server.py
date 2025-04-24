import asyncio
import websockets
import json
import pandas as pd

EXCEL_FILE_PATH = "/Users/leviwheeling/Documents/talk_to_mushrooms/Comp_min__2025_02_02_09_20_32_MST_1.xlsx"

def read_latest_sensor_data():
    """Reads the latest environmental data from Excel and returns it as a dictionary."""
    try:
        # Load Excel file
        xls = pd.ExcelFile(EXCEL_FILE_PATH)
        sheet_name = xls.sheet_names[0]  # Read first sheet
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # Rename columns (ensure they match your data structure)
        df.columns = ["Line#", "Date", "Temperature", "Humidity", "CO2"]

        # Convert Date column to datetime format
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df = df.dropna(subset=["Date"]).sort_values(by="Date", ascending=False)  # Keep only valid timestamps

        # Get latest sensor reading
        latest = df.iloc[0]
        return {
            "timestamp": latest["Date"].strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": f"{latest['Temperature']}°F",
            "humidity": f"{latest['Humidity']}%",
            "CO2": f"{latest['CO2']} ppm"
        }
    except Exception as e:
        print("❌ Error reading sensor data:", e)
        return None

async def send_sensor_data(websocket):
    try:
        # Access the path via websocket.path if needed.
        print(f"🔗 Client connected: {websocket.path}")
        while True:
            data = read_latest_sensor_data()
            if data:
                print(f"📡 Sending data: {data}")
                await websocket.send(json.dumps(data))
            await asyncio.sleep(5)  # Update every 5 seconds
    except websockets.exceptions.ConnectionClosedError:
        print("⚠️ WebSocket client disconnected.")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

async def main():
    try:
        server = await websockets.serve(send_sensor_data, "0.0.0.0", 8765, ping_interval=10, ping_timeout=20)
        print("✅ WebSocket server started on ws://0.0.0.0:8765")
        await server.wait_closed()  # Keep server running
    except Exception as e:
        print(f"❌ WebSocket server failed to start: {e}")

# Ensure the event loop is started correctly
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())