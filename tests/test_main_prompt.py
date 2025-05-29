import unittest
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the function from main.py
from main import generate_mushroom_prompt

class TestMainPrompt(unittest.TestCase):

    def test_generate_mushroom_prompt_structure_and_data_insertion(self):
        """
        Test that generate_mushroom_prompt includes key sections and correctly inserts
        current and historical sensor data.
        """
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sensor_data = {
            "timestamp": current_time_str,
            "temperature": 45.5,
            "humidity": 98.2,
            "CO2": 480
        }
        
        history_data = [
            {
                "timestamp": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": 42.0,
                "humidity": 99.0,
                "CO2": 460
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": 43.0,
                "humidity": 97.5,
                "CO2": 470
            }
        ]

        prompt = generate_mushroom_prompt(sensor_data, history_data)

        # Check for overall structure
        self.assertIn("🍄 *Hello, dear caretaker...* 🍄", prompt)
        self.assertIn("**Current Conditions:**", prompt)
        self.assertIn("**I remember my past well…**", prompt)
        self.assertIn("Speak to me, tell me your thoughts, and I shall respond with my fungal wisdom.", prompt)

        # Check for current sensor data insertion (using f-string for clarity, actual check is In)
        self.assertIn(f"Time:** {sensor_data['timestamp']}", prompt)
        self.assertIn(f"Humidity:** {sensor_data['humidity']}", prompt)
        self.assertIn(f"CO₂ Levels:** {sensor_data['CO2']}", prompt)
        self.assertIn(f"Temperature:** {sensor_data['temperature']}", prompt)

        # Check for historical data insertion (at least one entry)
        # Example: - 2023-10-27 10:00:00: CO₂ 460 ppm, Humidity 99.0%, Temp 42.0°F
        history_entry_1_str = (
            f"- {history_data[0]['timestamp']}: CO₂ {history_data[0]['CO2']} ppm, "
            f"Humidity {history_data[0]['humidity']}%, Temp {history_data[0]['temperature']}°F"
        )
        self.assertIn(history_entry_1_str, prompt)
        
        history_entry_2_str = (
            f"- {history_data[1]['timestamp']}: CO₂ {history_data[1]['CO2']} ppm, "
            f"Humidity {history_data[1]['humidity']}%, Temp {history_data[1]['temperature']}°F"
        )
        self.assertIn(history_entry_2_str, prompt)

    def test_generate_mushroom_prompt_empty_history(self):
        """Test prompt generation with empty history data."""
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor_data = {
            "timestamp": current_time_str,
            "temperature": 46.0,
            "humidity": 97.0,
            "CO2": 490
        }
        history_data = [] # Empty history

        prompt = generate_mushroom_prompt(sensor_data, history_data)

        self.assertIn("**Current Conditions:**", prompt)
        self.assertIn(f"Temperature:** {sensor_data['temperature']}", prompt)
        # Check that the history section is present but implies emptiness or is just the header
        self.assertIn("**I remember my past well…**", prompt)
        # The loop `history_text = "\n".join([...])` will result in an empty string if history_data is empty.
        # So, we expect the prompt to be generated without error, and the history section to be minimal.
        # The exact text after "Here’s how I’ve been doing over time:" would be just a newline if history_text is empty.
        self.assertTrue(prompt.strip().endswith("Speak to me, tell me your thoughts, and I shall respond with my fungal wisdom."))


    def test_generate_mushroom_prompt_no_key_error(self):
        """
        Test that no KeyError occurs with valid dictionary structures,
        even if some values might be None (though current data generation doesn't produce None).
        The function itself doesn't explicitly handle None values for formatting,
        so this test primarily ensures correct key access.
        """
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor_data = {
            "timestamp": current_time_str,
            "temperature": 45.5,
            "humidity": 98.2,
            "CO2": 480
            # Missing other potential keys, but the function only uses these
        }
        
        history_data = [
            {
                "timestamp": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": 42.0,
                "humidity": 99.0,
                "CO2": 460
            },
            # A history entry with potentially missing non-essential keys (if any existed)
            # For this function, all listed keys (timestamp, CO2, humidity, temperature) are essential for the f-string.
        ]

        try:
            generate_mushroom_prompt(sensor_data, history_data)
        except KeyError as e:
            self.fail(f"generate_mushroom_prompt raised KeyError unexpectedly: {e}")

if __name__ == '__main__':
    # Need to import timedelta for the test data generation
    from datetime import timedelta
    unittest.main()
