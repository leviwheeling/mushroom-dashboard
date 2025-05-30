import random
from datetime import datetime, timedelta
import time # For __main__ block sleep

# Define Zone Names
ZONE_NAMES = ["Babylon 1", "Babylon 2", "Mine", "Tent 1", "Tent 2", "Bear Mountain"]

# Global dictionary to store pseudo sensor history for each zone
SENSOR_HISTORY = {}

def get_zone_index(zone_name: str) -> int:
    # Helper to get a consistent index for zone-based variations
    if zone_name in ZONE_NAMES:
        return ZONE_NAMES.index(zone_name)
    # Fallback for unknown zones, though ideally zone_name should always be valid
    return -1 

def generate_pseudo_sensor_data(base_time=None, zone_name: str = None):
    """
    Generate pseudo sensor data, now with zone-specific variations.
    
    Parameters:
      base_time (datetime): If provided, use it as the timestamp; otherwise, use now.
      zone_name (str): The name of the zone for which to generate data. Required.
    
    Returns a dictionary with:
      - "timestamp": current time as "YYYY-MM-DD HH:MM:SS"
      - "temperature": normally between 40.0°F and 50.0°F (with zone variations)
      - "humidity": normally between 95.0% and 100.0% (with zone variations)
      - "CO2": normally between 440 and 500 ppm (with zone variations)
      - "zone": the provided zone_name
      
    Zone-based variations (deterministic):
      - Temperature: Varies slightly per zone.
      - Humidity: Varies slightly per zone.
      - CO2: Varies slightly per zone.
    Occasionally (≈1 anomaly per day if readings are every 5 mins), generate an anomalous reading.
    """
    if zone_name is None:
        raise ValueError("zone_name must be provided to generate_pseudo_sensor_data")
    if zone_name not in ZONE_NAMES:
        # This helps catch issues if an invalid zone name is passed
        print(f"Warning: '{zone_name}' is not a predefined zone. Using default variations.")
        zone_idx = -1 # Default to no specific variation or handle as error
    else:
        zone_idx = get_zone_index(zone_name)

    if base_time is None:
        base_time = datetime.now()
    
    # Base values - these can be adjusted per zone
    base_temp_min, base_temp_max = 40.0, 50.0
    base_humidity_min, base_humidity_max = 95.0, 100.0 # Healthy mushrooms like high humidity
    base_co2_min, base_co2_max = 440, 500 # Lower CO2 is generally better

    # Apply deterministic zone variations
    # Example: Zone index shifts the range. 
    # Using modulo to cycle variations for more than a few zones if needed,
    # or just simple linear shift based on index.
    # For 6 zones, (idx - 2.5) gives a spread around 0.
    # Mine (idx 2) -> -0.5 offset factor
    # Tent 2 (idx 4) -> +1.5 offset factor
    offset_factor = (zone_idx - (len(ZONE_NAMES) -1) / 2.0) # e.g. for 6 zones, indices 0-5, (len-1)/2 = 2.5. Results in -2.5 to 2.5
    
    temp_offset = offset_factor * 0.8  # Each zone can vary by up to +/- 2F from base if 6 zones (0.8 * 2.5)
    humidity_offset = offset_factor * -1.0 # Higher index = slightly less humid (max -2.5%)
    co2_offset = offset_factor * 15 # Higher index = slightly higher CO2 (max +37ppm)

    current_temp_min = base_temp_min + temp_offset
    current_temp_max = base_temp_max + temp_offset
    current_humidity_min = max(85.0, base_humidity_min + humidity_offset) # Ensure humidity doesn't go unrealistically low
    current_humidity_max = min(100.0, base_humidity_max + humidity_offset) # Cap at 100%
    current_co2_min = max(300, base_co2_min + int(co2_offset))
    current_co2_max = max(350, base_co2_max + int(co2_offset)) # Ensure CO2 doesn't go too low
    
    # Anomaly probability: approx 1 per day for 5-min interval history, 1 per 2 hours for live data (5s interval)
    # For history (5-min interval = 288 readings/day), prob = 1/288
    # For live (5s interval = 17280 readings/day), prob = 1/(24*12) (if live is every 5 min)
    # Let's assume this function is used for both, so pick a general one, or adjust if context is known
    anomaly_probability = 1 / (24 * 12) # Approx 1 anomaly per day if readings are every 5 mins

    if random.random() < anomaly_probability:
        temperature = round(random.uniform(current_temp_max + 5, current_temp_max + 15), 1) # Anomaly is warmer
        humidity = round(random.uniform(max(70.0, current_humidity_min - 20), current_humidity_min - 10), 1) # Anomaly is drier
        CO2 = random.randint(current_co2_max + 100, current_co2_max + 300) # Anomaly is higher CO2
    else:
        temperature = round(random.uniform(current_temp_min, current_temp_max), 1)
        humidity = round(random.uniform(current_humidity_min, current_humidity_max), 1)
        CO2 = random.randint(current_co2_min, current_co2_max)
        
    return {
        "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": temperature,
        "humidity": humidity,
        "CO2": CO2,
        "zone": zone_name # Ensure zone name is part of the record
    }

def initialize_history():
    """
    Initializes SENSOR_HISTORY for all defined zones with one week of data.
    A reading is simulated every 5 minutes from one week ago until now for each zone.
    """
    global SENSOR_HISTORY
    SENSOR_HISTORY = {} 
    now = datetime.now()
    
    print("Initializing sensor history for all zones...")

    for zone_name_iter in ZONE_NAMES: 
        print(f"  Initializing history for zone: {zone_name_iter}...")
        SENSOR_HISTORY[zone_name_iter] = []
        start_time = now - timedelta(days=7)
        interval = timedelta(minutes=5) 
        current_time = start_time
        while current_time <= now:
            data = generate_pseudo_sensor_data(base_time=current_time, zone_name=zone_name_iter)
            SENSOR_HISTORY[zone_name_iter].append(data)
            current_time += interval
    print("Sensor history initialization complete.")


def read_sensor_data(zone_name: str):
    """
    Simulate reading sensor data for a specific zone.
    If SENSOR_HISTORY is empty or the zone_name's history is missing/empty, 
    it calls initialize_history() first.
    Generates a new reading 5 seconds after the last reading for that zone.
    
    Parameters:
      zone_name (str): The name of the zone to read data for.
      
    Returns:
      (latest_sensor_data_for_zone, full_history_for_zone)
    
    Raises:
        ValueError: if the provided zone_name is not in ZONE_NAMES.
    """
    global SENSOR_HISTORY

    if zone_name not in ZONE_NAMES:
        raise ValueError(f"Unknown zone_name: '{zone_name}'. Must be one of {ZONE_NAMES}")

    if not SENSOR_HISTORY or zone_name not in SENSOR_HISTORY or not SENSOR_HISTORY[zone_name]:
        print(f"History not initialized or zone '{zone_name}' missing/empty. Initializing all zone histories...")
        initialize_history() 

    if not SENSOR_HISTORY[zone_name]: 
        print(f"Warning: History for zone '{zone_name}' remains empty after initialization. Generating a new reading from 'now'.")
        # This indicates an issue, perhaps initialize_history didn't populate this zone.
        # For robustness, create a starting point.
        last_timestamp_dt = datetime.now() - timedelta(seconds=5) 
    else:
        last_reading = SENSOR_HISTORY[zone_name][-1]
        last_timestamp_dt = datetime.strptime(last_reading["timestamp"], "%Y-%m-%d %H:%M:%S")

    new_timestamp_dt = last_timestamp_dt + timedelta(seconds=5) 
    new_data = generate_pseudo_sensor_data(base_time=new_timestamp_dt, zone_name=zone_name)
    SENSOR_HISTORY[zone_name].append(new_data)
    
    return new_data, SENSOR_HISTORY[zone_name]


if __name__ == "__main__":
    print("--- Sensor Handler Demonstration (Multi-Zone) ---")
    # initialize_history() is called by read_sensor_data if needed,
    # but calling it explicitly here ensures all zones are populated for the demo.
    initialize_history() 

    print("\n--- Reading data for specific zones ---")
    
    demo_zones = ["Babylon 1", "Mine", ZONE_NAMES[-1]] # Test first, one from middle, and last

    for zone_demo_name in demo_zones:
        print(f"\n--- {zone_demo_name} ---")
        try:
            latest_data, history_data = read_sensor_data(zone_name=zone_demo_name)
            print(f"📊 Latest Sensor Data for {zone_demo_name}:", latest_data)
            print(f"📜 Last 3 entries of Sensor History for {zone_demo_name}:")
            for entry in history_data[-3:]:
                print(entry)
            
            # Simulate another reading
            if len(demo_zones) == 1: # Only if testing single zone to avoid too much delay
                time.sleep(1) 
                latest_data_next, _ = read_sensor_data(zone_name=zone_demo_name)
                print(f"📊 Next Sensor Data for {zone_demo_name} (after 1s):", latest_data_next)

        except ValueError as e:
            print(f"Error for {zone_demo_name}: {e}")

    print(f"\nTotal zones in SENSOR_HISTORY: {len(SENSOR_HISTORY)}")
    for zn in ZONE_NAMES:
        if zn in SENSOR_HISTORY:
            print(f"Number of readings for '{zn}': {len(SENSOR_HISTORY[zn])}")
        else:
            print(f"No history found for '{zn}'")

    print("\n--- Zone Variation Sanity Check (first historical entry) ---")
    for zone_name_check in ZONE_NAMES:
        if SENSOR_HISTORY.get(zone_name_check) and len(SENSOR_HISTORY[zone_name_check]) > 0:
            first_entry = SENSOR_HISTORY[zone_name_check][0]
            print(f"Zone: {first_entry['zone']}, Temp: {first_entry['temperature']:.1f}, Hum: {first_entry['humidity']:.1f}, CO2: {first_entry['CO2']}")
        else:
            print(f"No history found for {zone_name_check} for variation check.")
