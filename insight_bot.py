import os
import json
from openai import OpenAI
from sensor_handler import read_sensor_data

# Read API key from file
def get_api_key():
    try:
        with open('key.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception("key.txt not found. Please create it from key.template.txt")

api_key = get_api_key()
client = OpenAI(api_key=api_key)

# Set the Insight Bot assistant ID (your insight bot)
INSIGHT_ASSISTANT_ID = "asst_0MNEOfvkS0W29towhYCUXqZS"

# Global variables to maintain conversation thread and track the last insight timestamp.
INSIGHT_THREAD_ID = None
LAST_INSIGHT_TIMESTAMP = None

def start_conversation():
    """Creates a new Thread for the Insight Bot and stores its thread ID."""
    global INSIGHT_THREAD_ID
    thread = client.beta.threads.create()
    INSIGHT_THREAD_ID = thread.id
    return INSIGHT_THREAD_ID

def send_message(thread_id, user_message):
    """Sends a message to the Insight Bot and retrieves its response."""
    try:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=INSIGHT_ASSISTANT_ID
        )
        messages = client.beta.threads.messages.list(thread_id=thread_id)
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

    latest, history = read_sensor_data()
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
    try:
        response_json = json.loads(response_str)
        if all(k in response_json for k in ["historicalSummary", "currentReading", "insight"]):
            return response_json
        else:
            return {
                "historicalSummary": "",
                "currentReading": "",
                "insight": response_str
            }
    except Exception as e:
        return {
            "historicalSummary": "",
            "currentReading": "",
            "insight": response_str
        }

if __name__ == "__main__":
    insight = get_insight()
    print("Insight Bot output:")
    print(insight)