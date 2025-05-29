import sys
from app_config import get_openai_client
from sensor_handler import get_latest_sensor_data_and_history

# --- Configuration and Setup ---
try:
    CLIENT = get_openai_client()
except FileNotFoundError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
except Exception as e: # Catch any other exception from app_config.load_api_key
    print(f"❌ ERROR: An unexpected error occurred during setup: {e}")
    sys.exit(1)

# OpenAI Assistant ID
ASSISTANT_ID = "asst_GOHjtf7WMJMji6d5VEjxwuDY" # 🔒 Keep this or manage it via config too

# Start a new conversation
def start_conversation():
    """Creates a new AI conversation thread."""
    return CLIENT.beta.threads.create().id

# Send messages to AI
def send_message(thread_id, user_message):
    """Sends a message to OpenAI and returns the response."""
    try:
        CLIENT.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_message
        )
        run = CLIENT.beta.threads.runs.create_and_poll(
            thread_id=thread_id, assistant_id=ASSISTANT_ID
        )
        messages = CLIENT.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text.value
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"

# Create immersive mushroom dialogue
def generate_mushroom_prompt(sensor_data, history_data):
    """Formats a mushroom AI prompt using both current and past sensor data."""
    # Keys for sensor_data were already correct: timestamp, humidity, CO2, temperature.
    # Updating keys for history_data processing:
    history_text = "\n".join(
        [f"- {entry['timestamp']}: CO₂ {entry['CO2']} ppm, Humidity {entry['humidity']}%, Temp {entry['temperature']}°F"
         for entry in history_data[:10]]  # Limit to last 10 entries
    )

    return f"""
    🍄 *Hello, dear caretaker...* 🍄  
    I am your ever-growing **mushroom**, deeply rooted in the underground.
    Through my gills, I have sensed the passing moments… Here’s how I feel now:

    **Current Conditions:**
    📅 **Time:** {sensor_data['timestamp']}
    🌿 **Humidity:** {sensor_data['humidity']}
    🌬️ **CO₂ Levels:** {sensor_data['CO2']}
    🔥 **Temperature:** {sensor_data['temperature']}

    **I remember my past well…**
    Here’s how I’ve been doing over time:
    {history_text}

    Speak to me, tell me your thoughts, and I shall respond with my fungal wisdom.
    """

def main():
    """Runs the Mushroom AI conversation system."""
    print("\n🌱 Welcome to 'Talk to Your Mushrooms' AI 🍄\n")

    thread_id = start_conversation()

    # Get sensor data
    sensor_data, history_data = get_latest_sensor_data_and_history()
    if not sensor_data or not history_data: # This check remains valid
        print("❌ ERROR: No sensor data available. Exiting.")
        return

    # Create immersive mushroom dialogue
    initial_prompt = generate_mushroom_prompt(sensor_data, history_data)

    # Send initial message
    print("\n🍄 Mushroom says:", send_message(thread_id, initial_prompt))

    # Chat loop
    while True:
        user_input = input("\n👨‍🌾 Caretaker: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\n🔚 The mushroom retreats into silence... Goodbye! 🍂\n")
            break

        # Send user message to AI and get response
        ai_response = send_message(thread_id, user_input)
        print("\n🍄 Mushroom says:", ai_response)

if __name__ == "__main__":
    main()