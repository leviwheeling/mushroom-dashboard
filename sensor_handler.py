import random
from datetime import datetime, timedelta

# Global list to store pseudo sensor history
SENSOR_HISTORY = []

def generate_pseudo_sensor_data(base_time=None):
    """
    Generate pseudo sensor data.
    
    Parameters:
      base_time (datetime): If provided, use it as the timestamp; otherwise, use now.
    
    Returns a dictionary with:
      - "timestamp": current time as "YYYY-MM-DD HH:MM:SS"
      - "temperature": normally between 40.0°F and 50.0°F
      - "humidity": normally between 95.0% and 100.0%
      - "CO2": normally between 440 and 500 ppm
      
    Occasionally (≈1 anomaly every 2 hours in live mode), generate an anomalous reading:
      - Temperature: 55–65°F
      - Humidity: 80–90%
      - CO2: 600–800 ppm
    """
    if base_time is None:
        base_time = datetime.now()
    # For live readings every 5 seconds, use a low anomaly probability.
    anomaly_probability = 1 / 1440  # roughly one anomaly every 1440 readings (~2 hours)
    if random.random() < anomaly_probability:
        temperature = round(random.uniform(55.0, 65.0), 2)
        humidity = round(random.uniform(80.0, 90.0), 2)
        CO2 = random.randint(600, 800)
    else:
        temperature = round(random.uniform(40.0, 50.0), 2)
        humidity = round(random.uniform(95.0, 100.0), 2)
        CO2 = random.randint(440, 500)
    return {
        "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": temperature,
        "humidity": humidity,
        "CO2": CO2
    }

def initialize_history():
    """
    Initializes SENSOR_HISTORY with one week of data if it's empty.
    A reading is simulated every 5 minutes from one week ago until now.
    """
    global SENSOR_HISTORY
    if not SENSOR_HISTORY: # Only initialize if it's actually empty
        now = datetime.now()
        start_time = now - timedelta(days=7)
        interval = timedelta(minutes=5)
        current_time = start_time
        temp_history = []
        while current_time <= now:
            data = generate_pseudo_sensor_data(current_time)
            temp_history.append(data)
            current_time += interval
        SENSOR_HISTORY = temp_history

def get_latest_sensor_data_and_history():
    """
    Retrieves the latest sensor data and the full sensor history.
    If SENSOR_HISTORY is empty, it initializes it first.
    This function does NOT generate new sensor data.

    Returns:
      (latest_sensor_data, full_history) or (None, []) if history is empty after init.
    """
    global SENSOR_HISTORY
    if not SENSOR_HISTORY:
        initialize_history()
    
    if not SENSOR_HISTORY: # If still empty after initialization
        return None, []
        
    return SENSOR_HISTORY[-1], SENSOR_HISTORY

def generate_and_add_new_reading():
    """
    Generates a new sensor reading and adds it to SENSOR_HISTORY.
    If SENSOR_HISTORY is empty, it calls initialize_history() first to ensure there's a baseline.
    The new reading is timestamped 5 seconds after the last reading in SENSOR_HISTORY,
    or based on the current time if SENSOR_HISTORY was initially empty and initialize_history()
    did not populate it (which shouldn't happen with current logic).

    Returns:
      The newly generated data point.
    """
    global SENSOR_HISTORY
    if not SENSOR_HISTORY:
        initialize_history() 

    if not SENSOR_HISTORY:
        # This case implies initialize_history() didn't populate SENSOR_HISTORY.
        # Generate a reading based on datetime.now() as a fallback.
        new_time = datetime.now()
    else:
        last_reading = SENSOR_HISTORY[-1]
        last_time = datetime.strptime(last_reading["timestamp"], "%Y-%m-%d %H:%M:%S")
        new_time = last_time + timedelta(seconds=5)
    
    new_data = generate_pseudo_sensor_data(new_time)
    SENSOR_HISTORY.append(new_data)
    return new_data

if __name__ == "__main__":
    print("--- Sensor Handler Test Script ---")
    
    print("\n1. Attempting to get latest data and history (should initialize if empty)...")
    latest_data, full_history = get_latest_sensor_data_and_history()
    if latest_data:
        print(f"   📊 Initial Latest Sensor Data: Timestamp {latest_data['timestamp']}")
        print(f"   📜 Initial Full Sensor History has {len(full_history)} entries.")
        print("   📜 Last 2 entries of Initial History:")
        for entry in full_history[-2:]:
            print(f"     {entry}")
    else:
        print("   ⚠️ No sensor data available even after attempting initialization.")

    print("\n2. Generating a new sensor reading...")
    new_reading = generate_and_add_new_reading()
    print(f"   ✨ Newly Generated Sensor Data: Timestamp {new_reading['timestamp']}, Temp {new_reading['temperature']}°F")

    print("\n3. Getting latest data and history again (should reflect the new reading)...")
    latest_data_after_new, full_history_after_new = get_latest_sensor_data_and_history()
    if latest_data_after_new:
        print(f"   📊 Latest Sensor Data after generation: Timestamp {latest_data_after_new['timestamp']}")
        assert latest_data_after_new["timestamp"] == new_reading["timestamp"], "Error: Latest data doesn't match new reading!"
        print(f"   📜 Full Sensor History now has {len(full_history_after_new)} entries.")
        print("   📜 Last 2 entries of Updated History:")
        for entry in full_history_after_new[-2:]:
            print(f"     {entry}")
    else:
        print("   ⚠️ No sensor data available after generating new reading.")

    print("\n4. Generating another new sensor reading...")
    another_new_reading = generate_and_add_new_reading()
    print(f"   ✨ Another Newly Generated Sensor Data: Timestamp {another_new_reading['timestamp']}, Temp {another_new_reading['temperature']}°F")

    print("\n5. Final check of latest data and history...")
    latest_data_final, full_history_final = get_latest_sensor_data_and_history()
    if latest_data_final:
        print(f"   📊 Final Latest Sensor Data: Timestamp {latest_data_final['timestamp']}")
        assert latest_data_final["timestamp"] == another_new_reading["timestamp"], "Error: Latest data doesn't match the second new reading!"
        print(f"   📜 Final Full Sensor History has {len(full_history_final)} entries.")
        print("   📜 Last 2 entries of Final History:")
        for entry in full_history_final[-2:]:
            print(f"     {entry}")
    else:
        print("   ⚠️ No sensor data available at the end.")
    
    print("\n--- Test Script Finished ---")