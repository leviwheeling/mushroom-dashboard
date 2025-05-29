import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the modules/functions
from insight_bot import compute_summary, get_insight
import insight_bot # For resetting globals
import sensor_handler # For test data setup

class TestInsightBot(unittest.TestCase):

    def setUp(self):
        """Reset globals from insight_bot and sensor_handler if necessary."""
        insight_bot.INSIGHT_THREAD_ID = None
        insight_bot.LAST_INSIGHT_TIMESTAMP = None
        sensor_handler.SENSOR_HISTORY = []
        # Ensure client is mocked or won't be called in these tests
        # Patching send_message should prevent actual client usage for get_insight tests.
        # For compute_summary, client is not used.

    def test_compute_summary_valid_data(self):
        history = [
            {"temperature": 10, "humidity": 60, "CO2": 400, "timestamp": "t1"},
            {"temperature": 20, "humidity": 70, "CO2": 500, "timestamp": "t2"},
            {"temperature": 30, "humidity": 80, "CO2": 600, "timestamp": "t3"},
        ]
        summary = compute_summary(history)
        self.assertEqual(summary["temperature"]["min"], 10)
        self.assertEqual(summary["temperature"]["max"], 30)
        self.assertEqual(summary["temperature"]["avg"], 20)
        self.assertEqual(summary["humidity"]["min"], 60)
        self.assertEqual(summary["humidity"]["max"], 80)
        self.assertEqual(summary["humidity"]["avg"], 70)
        self.assertEqual(summary["CO2"]["min"], 400)
        self.assertEqual(summary["CO2"]["max"], 600)
        self.assertEqual(summary["CO2"]["avg"], 500)

    def test_compute_summary_empty_history(self):
        history = []
        summary = compute_summary(history)
        self.assertIsNone(summary["temperature"]["min"])
        self.assertIsNone(summary["temperature"]["max"])
        self.assertIsNone(summary["temperature"]["avg"])
        # ... and so on for humidity and CO2

    def test_compute_summary_with_none_values(self):
        history = [
            {"temperature": 10, "humidity": None, "CO2": 400, "timestamp": "t1"},
            {"temperature": None, "humidity": 70, "CO2": 500, "timestamp": "t2"},
            {"temperature": 30, "humidity": 80, "CO2": None, "timestamp": "t3"},
            {"temperature": 20, "humidity": 75, "CO2": 450, "timestamp": "t4"},
        ]
        summary = compute_summary(history)
        self.assertEqual(summary["temperature"]["min"], 10)
        self.assertEqual(summary["temperature"]["max"], 30)
        self.assertEqual(summary["temperature"]["avg"], 20) # (10+30+20)/3
        self.assertEqual(summary["humidity"]["min"], 70)
        self.assertEqual(summary["humidity"]["max"], 80)
        self.assertEqual(summary["humidity"]["avg"], 75) # (70+80+75)/3
        self.assertEqual(summary["CO2"]["min"], 400)
        self.assertEqual(summary["CO2"]["max"], 500)
        self.assertEqual(summary["CO2"]["avg"], 450) # (400+500+450)/3

    @patch('insight_bot.get_latest_sensor_data_and_history')
    @patch('insight_bot.send_message')
    @patch('insight_bot.initialize_client') # Ensure OpenAI client isn't actually init'd
    def test_get_insight_valid_response(self, mock_init_client, mock_send_msg, mock_get_sensor_data):
        # Setup Mocks
        latest_data = {"timestamp": "2023-01-01 12:00:00", "temperature": 25, "humidity": 60, "CO2": 450}
        history_data = [{"timestamp": "2023-01-01 11:00:00", "temperature": 24, "humidity": 62, "CO2": 440}]
        mock_get_sensor_data.return_value = (latest_data, history_data)
        
        ai_response_json = {
            "historicalSummary": "Temp avg 24.5°F",
            "currentReading": "Temp 25°F",
            "insight": "All good. Fun fact: ...",
        }
        mock_send_msg.return_value = json.dumps(ai_response_json)

        # Call function
        result = get_insight()

        # Assertions
        self.assertEqual(result, ai_response_json)
        self.assertEqual(insight_bot.LAST_INSIGHT_TIMESTAMP, "2023-01-01 12:00:00")
        mock_send_msg.assert_called_once() # Check that AI was called
        mock_init_client.assert_called() # Check that client initialization was attempted

    @patch('insight_bot.get_latest_sensor_data_and_history')
    @patch('insight_bot.send_message')
    @patch('insight_bot.initialize_client')
    def test_get_insight_json_decode_error(self, mock_init_client, mock_send_msg, mock_get_sensor_data):
        latest_data = {"timestamp": "2023-01-01 12:00:00", "temperature": 25, "humidity": 60, "CO2": 450}
        history_data = [{"timestamp": "2023-01-01 11:00:00", "temperature": 24, "humidity": 62, "CO2": 440}]
        mock_get_sensor_data.return_value = (latest_data, history_data)
        
        mock_send_msg.return_value = "This is not valid JSON"

        result = get_insight()
        self.assertIn("error", result)
        self.assertEqual(result["error"], "AI response processing failed")
        self.assertIn("Could not parse JSON response from AI", result["details"])
        self.assertEqual(result["original_response"][:50], "This is not valid JSON"[:50]) # Check snippet

    @patch('insight_bot.get_latest_sensor_data_and_history')
    @patch('insight_bot.send_message')
    @patch('insight_bot.initialize_client')
    def test_get_insight_missing_keys_in_response(self, mock_init_client, mock_send_msg, mock_get_sensor_data):
        latest_data = {"timestamp": "2023-01-01 12:00:00", "temperature": 25, "humidity": 60, "CO2": 450}
        history_data = [{"timestamp": "2023-01-01 11:00:00", "temperature": 24, "humidity": 62, "CO2": 440}]
        mock_get_sensor_data.return_value = (latest_data, history_data)
        
        ai_response_json = {"historicalSummary": "Summary", "currentReading": "Reading"} # Missing "insight"
        mock_send_msg.return_value = json.dumps(ai_response_json)

        result = get_insight()
        self.assertIn("error", result)
        self.assertEqual(result["error"], "AI response processing failed")
        self.assertIn("Missing expected keys in AI response", result["details"])

    @patch('insight_bot.get_latest_sensor_data_and_history')
    @patch('insight_bot.send_message') # Still need to mock this even if not called
    @patch('insight_bot.initialize_client')
    def test_get_insight_no_sensor_data(self, mock_init_client, mock_send_msg, mock_get_sensor_data):
        mock_get_sensor_data.return_value = (None, []) # Simulate no sensor data

        result = get_insight()
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Sensor data unavailable")
        self.assertEqual(result["insight"], "Insight generation failed due to missing sensor data.")
        mock_send_msg.assert_not_called() # AI should not be called if sensor data is missing

    @patch('insight_bot.get_latest_sensor_data_and_history')
    @patch('insight_bot.send_message')
    @patch('insight_bot.initialize_client')
    def test_get_insight_thread_creation(self, mock_init_client, mock_send_msg, mock_get_sensor_data):
        # This test checks if start_conversation is called when INSIGHT_THREAD_ID is None
        self.assertIsNone(insight_bot.INSIGHT_THREAD_ID) # Should be None from setUp

        latest_data = {"timestamp": "2023-01-01 12:00:00", "temperature": 25, "humidity": 60, "CO2": 450}
        history_data = [{"timestamp": "2023-01-01 11:00:00", "temperature": 24, "humidity": 62, "CO2": 440}]
        mock_get_sensor_data.return_value = (latest_data, history_data)
        
        ai_response_json = {"historicalSummary": "S", "currentReading": "C", "insight": "I"}
        mock_send_msg.return_value = json.dumps(ai_response_json)

        # Mock start_conversation specifically for this test to check its call
        with patch('insight_bot.start_conversation', return_value="test_thread_123") as mock_start_conv:
            get_insight()
            mock_start_conv.assert_called_once() # start_conversation should be called
            self.assertEqual(insight_bot.INSIGHT_THREAD_ID, "test_thread_123")

            # Call again, start_conversation should not be called again
            get_insight()
            mock_start_conv.assert_called_once() # Still called only once in total


if __name__ == '__main__':
    unittest.main()
