import sys # For sys.exit in the main block
from app_config import get_openai_client

# Initialize OpenAI client via app_config
# Let exceptions from get_openai_client propagate if this module is imported.
# The main block below will handle them for direct execution.
CLIENT = None # Initialize to None, will be set in the main block or by importer

# Replace this with your actual Assistant ID from OpenAI
ASSISTANT_ID = "asst_GOHjtf7WMJMji6d5VEjxwuDY"

def initialize_client():
    """Initializes the OpenAI client."""
    global CLIENT
    if CLIENT is None:
        CLIENT = get_openai_client()

def start_conversation():
    """Creates a new Thread for the Assistant to track messages."""
    initialize_client() # Ensure client is initialized
    thread = CLIENT.beta.threads.create()
    return thread.id  # Return the thread ID for tracking history

def send_message(thread_id, user_message):
    """Sends a message to the Assistant and retrieves its response."""
    initialize_client() # Ensure client is initialized
    try:
        # Add the user message to the thread
        CLIENT.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Run the Assistant on this thread
        run = CLIENT.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Retrieve the Assistant's response
        messages = CLIENT.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text.value  # Extract assistant's reply

    except Exception as e:
        return f"Error generating AI response: {str(e)}"

if __name__ == "__main__":
    # Start a new conversation thread
    try:
        initialize_client() # Initialize client for standalone execution
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred during setup: {e}")
        sys.exit(1)

    thread_id = start_conversation()

    # Example sensor data
    initial_sensor_data = {
        "humidity": "85%",
        "CO2": "1200 ppm",
        "light": "300 lux",
        "airflow": "0.8 m/s",
        "weight": "250g",
        "type": "oyster"
    }

    # Send the initial sensor data as a message to the Assistant
    initial_prompt = f"""
    Humidity: {initial_sensor_data.get('humidity')}
    CO2 Levels: {initial_sensor_data.get('CO2')}
    Light Intensity: {initial_sensor_data.get('light')}
    Airflow: {initial_sensor_data.get('airflow')}
    Weight: {initial_sensor_data.get('weight')}
    Type: {initial_sensor_data.get('type')}
    """

    # Send sensor data to the Assistant
    print("Mushroom says:", send_message(thread_id, initial_prompt))

    # Continuous conversation loop
    while True:
        user_input = input("\nCaretaker: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting conversation. Goodbye!")
            break

        # Send user input to Assistant and print response
        ai_response = send_message(thread_id, user_input)
        print("\nMushroom says:", ai_response)