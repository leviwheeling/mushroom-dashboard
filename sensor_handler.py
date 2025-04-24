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
    Initializes SENSOR_HISTORY with one week of data.
    A reading is simulated every 5 minutes from one week ago until now.
    """
    global SENSOR_HISTORY
    SENSOR_HISTORY = []
    now = datetime.now()
    start_time = now - timedelta(days=7)
    interval = timedelta(minutes=5)
    current_time = start_time
    while current_time <= now:
        data = generate_pseudo_sensor_data(current_time)
        SENSOR_HISTORY.append(data)
        current_time += interval

def read_sensor_data():
    """
    Simulate reading sensor data:
      - If SENSOR_HISTORY is empty, initialize it with one week's data.
      - Otherwise, generate a new reading 5 seconds after the last reading.
    
    Returns:
      (latest_sensor_data, full_history)
    """
    global SENSOR_HISTORY
    if not SENSOR_HISTORY:
        initialize_history()
    last_reading = SENSOR_HISTORY[-1]
    last_time = datetime.strptime(last_reading["timestamp"], "%Y-%m-%d %H:%M:%S")
    new_time = last_time + timedelta(seconds=5)
    new_data = generate_pseudo_sensor_data(new_time)
    SENSOR_HISTORY.append(new_data)
    return new_data, SENSOR_HISTORY

if __name__ == "__main__":
    initialize_history()
    latest, history = read_sensor_data()
    print("📊 Latest Sensor Data:", latest)
    print("📜 Last 5 entries of Full Sensor History:")
    for entry in history[-5:]:
        print(entry)