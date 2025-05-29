import json
import sys # For sys.exit in the main block
from app_config import get_openai_client
from sensor_handler import get_latest_sensor_data_and_history, initialize_history as initialize_sensor_history

# Initialize OpenAI client via app_config
# Let exceptions from get_openai_client propagate if this module is imported.
# The main block below will handle them for direct execution.
CLIENT = None # Initialize to None, will be set in the main block or by importer

# Set the Insight Bot assistant ID (your insight bot)
INSIGHT_ASSISTANT_ID = "asst_0MNEOfvkS0W29towhYCUXqZS"

# Global variables to maintain conversation thread and track the last insight timestamp.
INSIGHT_THREAD_ID = None
LAST_INSIGHT_TIMESTAMP = None

def initialize_client():
    """Initializes the OpenAI client."""
    global CLIENT
    if CLIENT is None:
        CLIENT = get_openai_client()

def start_conversation():
    """Creates a new Thread for the Insight Bot and stores its thread ID."""
    global INSIGHT_THREAD_ID
    initialize_client() # Ensure client is initialized
    thread = CLIENT.beta.threads.create()
    INSIGHT_THREAD_ID = thread.id
    return INSIGHT_THREAD_ID

def send_message(thread_id, user_message):
    """Sends a message to the Insight Bot and retrieves its response."""
    initialize_client() # Ensure client is initialized
    try:
        CLIENT.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        run = CLIENT.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=INSIGHT_ASSISTANT_ID
        )
        messages = CLIENT.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text.value  # Extract the reply.
    except Exception as e:
        return f"Error generating AI response: {str(e)}"

def compute_summary(history):
    """
    Computes summary statistics (min, max, average) for Temperature, Humidity, and CO₂.
    """
    temps = [entry["temperature"] for entry in history if entry["temperature"] is not None]
    hums  = [entry["humidity"] for entry in history if entry["humidity"] is not None]
    co2s  = [entry["CO2"] for entry in history if entry["CO2"] is not None]
    
    summary = {
        "temperature": {
            "min": min(temps) if temps else None,
            "max": max(temps) if temps else None,
            "avg": round(sum(temps) / len(temps), 2) if temps else None,
        },
        "humidity": {
            "min": min(hums) if hums else None,
            "max": max(hums) if hums else None,
            "avg": round(sum(hums) / len(hums), 2) if hums else None,
        },
        "CO2": {
            "min": min(co2s) if co2s else None,
            "max": max(co2s) if co2s else None,
            "avg": round(sum(co2s) / len(co2s), 2) if co2s else None,
        }
    }
    return summary

def get_insight():
    """
    Retrieves current sensor data and historical readings, then uses only new entries (since the last insight)
    to compute summary statistics. Constructs a prompt that instructs the Insight Bot to output a JSON object with exactly
    three keys: "historicalSummary", "currentReading", and "insight". The response must be concise (no more than six sentences),
    flag any anomalies with ⚠️, and end with one fun fact about mushrooms.
    """
    global INSIGHT_THREAD_ID, LAST_INSIGHT_TIMESTAMP

    # Retrieve data without generating a new point
    latest, history = get_latest_sensor_data_and_history() 
    
    if not latest: # If no data, cannot generate insight
        return {
            "error": "Sensor data unavailable",
            "details": "Could not retrieve sensor data to generate insight.",
            "original_response": None,
            "historicalSummary": "Sensor data unavailable.",
            "currentReading": "Sensor data unavailable.",
            "insight": "Insight generation failed due to missing sensor data."
        }

    if LAST_INSIGHT_TIMESTAMP is None:
        new_history = history
    else:
        new_history = [entry for entry in history if entry["timestamp"] > LAST_INSIGHT_TIMESTAMP]

    LAST_INSIGHT_TIMESTAMP = latest["timestamp"]
    summary = compute_summary(new_history)

    prompt = (
        "Using the provided sensor data, produce a JSON object with exactly three keys: "
        "'historicalSummary', 'currentReading', and 'insight'. "
        "The 'historicalSummary' should concisely summarize the past week's data, for example: "
        "'Temperature: min " + str(summary['temperature']['min']) + "°F, max " + str(summary['temperature']['max']) +
        "°F, average " + str(summary['temperature']['avg']) + "°F; Humidity: min " + str(summary['humidity']['min']) +
        "%, max " + str(summary['humidity']['max']) + "%, average " + str(summary['humidity']['avg']) +
        "%; CO2: min " + str(summary['CO2']['min']) + " ppm, max " + str(summary['CO2']['max']) + " ppm, average " +
        str(summary['CO2']['avg']) + " ppm.' "
        "The 'currentReading' should report the latest sensor reading as: "
        "'Temperature: " + str(latest['temperature']) + "°F, Humidity: " + str(latest['humidity']) +
        "%, CO2: " + str(latest['CO2']) + " ppm.' "
        "Finally, the 'insight' key should contain a brief, insightful analysis (maximum six sentences) that compares the historical trends with the current reading, "
        "emphasizes that current conditions are optimal for mushroom growth, flags any discrepancies with the warning symbol (⚠️) if detected, and ends with one fun fact about mushrooms. "
        "Output only the JSON object without any additional text."
    )

    if INSIGHT_THREAD_ID is None:
        start_conversation()

    response_str = send_message(INSIGHT_THREAD_ID, prompt)
    
    error_response_template = {
        "error": "AI response processing failed",
        "original_response": response_str[:200] + "..." if response_str else "N/A", # Snippet
        "historicalSummary": "Error processing data.",
        "currentReading": "Error processing data.",
        "insight": "Error generating insight. Please check application logs or try again later."
    }

    try:
        response_json = json.loads(response_str)
        if all(k in response_json for k in ["historicalSummary", "currentReading", "insight"]):
            return response_json
        else:
            error_response_template["details"] = "Missing expected keys in AI response."
            return error_response_template
    except json.JSONDecodeError as e:
        error_response_template["details"] = f"Could not parse JSON response from AI: {e}"
        return error_response_template
    except Exception as e: # Catch any other unexpected error during processing
        error_response_template["details"] = f"An unexpected error occurred while processing AI response: {e}"
        return error_response_template

if __name__ == "__main__":
    try:
        # Initialize OpenAI client
        initialize_client() 
        # Initialize sensor history for standalone execution
        initialize_sensor_history()
    except FileNotFoundError as e:
        print(f"❌ ERROR (Setup): {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ ERROR (Setup): {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR (Setup): An unexpected error occurred during setup: {e}")
        sys.exit(1)
    
    print("Generating insight for standalone test...")
    insight = get_insight()
    print("\nInsight Bot output:")
    print(json.dumps(insight, indent=2))