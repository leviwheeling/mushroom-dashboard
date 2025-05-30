import json
from datetime import datetime 
from sensor_handler import read_sensor_data, ZONE_NAMES 
from ai_model import start_conversation as start_ai_conversation, send_message as send_ai_message

LAST_INSIGHT_TIMESTAMP = {} 

def compute_summary(history: list): 
    temps = [entry["temperature"] for entry in history if "temperature" in entry and entry["temperature"] is not None]
    hums  = [entry["humidity"] for entry in history if "humidity" in entry and entry["humidity"] is not None]
    co2s  = [entry["CO2"] for entry in history if "CO2" in entry and entry["CO2"] is not None]
    
    summary = {
        "temperature": {
            "min": min(temps) if temps else None,
            "max": max(temps) if temps else None,
            "avg": round(sum(temps) / len(temps), 1) if temps else None, # Adjusted to 1 decimal
        },
        "humidity": {
            "min": min(hums) if hums else None,
            "max": max(hums) if hums else None,
            "avg": round(sum(hums) / len(hums), 1) if hums else None, # Adjusted to 1 decimal
        },
        "CO2": {
            "min": min(co2s) if co2s else None,
            "max": max(co2s) if co2s else None,
            "avg": round(sum(co2s) / len(co2s), 0) if co2s else None, # CO2 as whole number
        }
    }
    return summary

def get_insight(zone_name: str):
    global LAST_INSIGHT_TIMESTAMP 

    if zone_name not in ZONE_NAMES:
        return {"error": f"Invalid zone_name: '{zone_name}'. Must be one of {ZONE_NAMES}"}

    try:
        latest, history = read_sensor_data(zone_name=zone_name)
    except ValueError as e: 
        return {"error": f"Could not read sensor data for zone '{zone_name}': {e}"}
    except Exception as e:
        return {"error": f"Unexpected error reading sensor data for zone '{zone_name}': {e}"}

    last_ts_for_zone = LAST_INSIGHT_TIMESTAMP.get(zone_name)
    new_history_for_summary = []

    if last_ts_for_zone is None:
        new_history_for_summary = history 
    else:
        try:
            last_dt = datetime.strptime(last_ts_for_zone, "%Y-%m-%d %H:%M:%S")
            new_history_for_summary = [entry for entry in history if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") > last_dt]
        except (ValueError, TypeError) as e: 
            print(f"Warning: Timestamp comparison error for zone {zone_name} (last_ts: {last_ts_for_zone}): {e}. Using full history.")
            new_history_for_summary = history

    if not new_history_for_summary and history: 
        print(f"No new sensor data for zone {zone_name} since {last_ts_for_zone}. Summarizing last day's worth of available entries.")
        # Approx last day if 5 min intervals (288 readings)
        new_history_for_summary = history[-288:] 
    elif not new_history_for_summary and not history:
         print(f"No history available at all for zone {zone_name} to generate summary.")
         # Return a structure indicating no data, so AI doesn't get empty fields
         summary = {"temperature": {}, "humidity": {}, "CO2": {}} # Empty summary
    else: # This case was missing, should be 'summary = compute_summary(new_history_for_summary)'
        summary = compute_summary(new_history_for_summary)


    LAST_INSIGHT_TIMESTAMP[zone_name] = latest["timestamp"] 

    temp_summary_str = f"Temperature: min {summary['temperature'].get('min','N/A')}°F, max {summary['temperature'].get('max','N/A')}°F, avg {summary['temperature'].get('avg','N/A')}°F"
    hum_summary_str = f"Humidity: min {summary['humidity'].get('min','N/A')}%, max {summary['humidity'].get('max','N/A')}%, avg {summary['humidity'].get('avg','N/A')}%"
    co2_summary_str = f"CO2: min {summary['CO2'].get('min','N/A')} ppm, max {summary['CO2'].get('max','N/A')} ppm, avg {summary['CO2'].get('avg','N/A')} ppm"
    
    current_reading_str = f"Temperature: {latest.get('temperature','N/A')}°F, Humidity: {latest.get('humidity','N/A')}%, CO2: {latest.get('CO2','N/A')} ppm"

    prompt = (
        f"You are an AI assistant for a mushroom farm, providing insights for Zone: '{zone_name}'.\n"
        "Based on the following data, produce a JSON object with exactly three keys: "
        "\"historicalSummary\", \"currentReading\", and \"insight\".\n" # Escaped quotes for JSON string
        "1. \"historicalSummary\": Concisely summarize the provided historical data.\n"
        f"   Historical data summary to use: {temp_summary_str}; {hum_summary_str}; {co2_summary_str}.\n"
        "2. \"currentReading\": Report the latest sensor reading.\n"
        f"   Current reading to use: {current_reading_str}.\n"
        "3. \"insight\": Provide a brief (max six sentences) analysis comparing historical trends with the current reading for this zone. "
        "Flag anomalies (e.g., readings outside typical ranges, or significant deviations from average) with EMOJI_WARNING. " # Placeholder for emoji
        "Conclude with one fun fact about mushrooms or mushroom cultivation. "
        "Output only the JSON object without any additional text or explanations."
    ).replace("EMOJI_WARNING", "⚠️") # Replace placeholder with actual emoji

    insight_thread_id = start_ai_conversation() 
    
    print(f"\nGenerating insight for zone: {zone_name} (Thread: {insight_thread_id})")
    
    response_str = send_ai_message(thread_id=insight_thread_id, user_message=prompt, zone_name=zone_name)
    
    try:
        response_json = json.loads(response_str)
        if isinstance(response_json, dict) and all(k in response_json for k in ["historicalSummary", "currentReading", "insight"]):
            return response_json
        else:
            print(f"Warning: AI response for zone {zone_name} was valid JSON but not the expected structure. Response: {response_str}")
            return {"error": "AI response format incorrect.", "raw_response": response_str}
    except json.JSONDecodeError:
        print(f"Warning: AI response for zone {zone_name} was not valid JSON. Response: {response_str}")
        return {"error": "AI response was not valid JSON.", "raw_response": response_str}
    except Exception as e:
        print(f"Error processing AI response for zone {zone_name}: {e}. Raw response: {response_str}")
        return {"error": f"Unexpected error processing AI response: {e}", "raw_response": response_str}

if __name__ == "__main__":
    print("--- Insight Bot Demonstration (Ollama & RAG - Multi-Zone) ---")
    example_zone = "Babylon 1" 
    if example_zone not in ZONE_NAMES:
        print(f"Error: '{example_zone}' is not a valid zone. Please choose from: {ZONE_NAMES}")
    else:
        insight_data = get_insight(zone_name=example_zone)
        print(f"\nInsight for Zone '{example_zone}':")
        print(json.dumps(insight_data, indent=2))

    example_zone_2 = "Mine"
    if example_zone_2 not in ZONE_NAMES:
        print(f"Error: '{example_zone_2}' is not a valid zone. Please choose from: {ZONE_NAMES}")
    else:
        insight_data_2 = get_insight(zone_name=example_zone_2)
        print(f"\nInsight for Zone '{example_zone_2}':")
        print(json.dumps(insight_data_2, indent=2))