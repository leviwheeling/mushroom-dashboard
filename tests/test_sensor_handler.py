import unittest
from datetime import datetime, timedelta
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the module
import sensor_handler

class TestSensorHandler(unittest.TestCase):

    def setUp(self):
        """Clear SENSOR_HISTORY before each test for isolation."""
        sensor_handler.SENSOR_HISTORY = []

    def test_initialize_history_populates_data(self):
        """Test that initialize_history populates SENSOR_HISTORY."""
        self.assertEqual(len(sensor_handler.SENSOR_HISTORY), 0)
        sensor_handler.initialize_history()
        self.assertTrue(len(sensor_handler.SENSOR_HISTORY) > 0)
        
        # Expected entries: 7 days * 24 hours/day * (60 minutes/hour / 5 minutes/entry) = 7 * 24 * 12 = 2016
        # Due to the way datetime.now() works, the exact number can vary slightly.
        # We'll check if it's close to the expected number.
        expected_min_entries = 2016 
        # If the test runs exactly at the turn of a 5-min interval, it might be one less,
        # or if it runs just after, it might be one more than a simple calculation.
        self.assertTrue(len(sensor_handler.SENSOR_HISTORY) >= expected_min_entries -1) 
        # Check structure of one entry
        self.assertIn("timestamp", sensor_handler.SENSOR_HISTORY[0])
        self.assertIn("temperature", sensor_handler.SENSOR_HISTORY[0])
        self.assertIn("humidity", sensor_handler.SENSOR_HISTORY[0])
        self.assertIn("CO2", sensor_handler.SENSOR_HISTORY[0])

    def test_initialize_history_reinitializes(self):
        """
        Test that calling initialize_history again re-initializes (clears and repopulates).
        The current implementation of initialize_history clears SENSOR_HISTORY first if it's not empty,
        then repopulates. So, subsequent calls will lead to a fresh list.
        """
        sensor_handler.initialize_history()
        first_timestamp_initial = sensor_handler.SENSOR_HISTORY[0]["timestamp"]
        initial_length = len(sensor_handler.SENSOR_HISTORY)

        # For the test to be meaningful, we need to ensure that a new call would generate
        # different data if it truly re-initializes from a potentially different "now".
        # However, if called immediately, "now" might be the same.
        # The key is that it *does* run the population logic again.
        # The prompt says "current code does allow re-initialization by clearing the list first"
        # The code was updated to `if not SENSOR_HISTORY: initialize`. So this test needs to reflect that.
        # If SENSOR_HISTORY is not empty, initialize_history will *not* run again.

        sensor_handler.initialize_history() # This call should NOT re-initialize now.
        second_timestamp_initial = sensor_handler.SENSOR_HISTORY[0]["timestamp"]
        second_length = len(sensor_handler.SENSOR_HISTORY)

        self.assertEqual(initial_length, second_length)
        self.assertEqual(first_timestamp_initial, second_timestamp_initial)

        # To test re-initialization, we'd have to clear it first.
        sensor_handler.SENSOR_HISTORY = [] # Manually clear
        sensor_handler.initialize_history() # Now it should run
        self.assertTrue(len(sensor_handler.SENSOR_HISTORY) > 0)


    def test_get_latest_sensor_data_and_history(self):
        """Test getting latest data without modifying history."""
        sensor_handler.initialize_history() # Populate history
        initial_length = len(sensor_handler.SENSOR_HISTORY)
        
        latest_data, history = sensor_handler.get_latest_sensor_data_and_history()
        
        self.assertIsNotNone(latest_data)
        self.assertIsNotNone(history)
        self.assertEqual(len(history), initial_length) # Length should not change
        self.assertEqual(latest_data, history[-1]) # Latest should be last element
        self.assertEqual(len(sensor_handler.SENSOR_HISTORY), initial_length) # Global history unchanged


    def test_get_latest_sensor_data_and_history_initializes_if_empty(self):
        """Test that get_latest_sensor_data_and_history initializes SENSOR_HISTORY if it's empty."""
        self.assertEqual(len(sensor_handler.SENSOR_HISTORY), 0) # Should be empty due to setUp
        
        latest_data, history = sensor_handler.get_latest_sensor_data_and_history()
        
        self.assertIsNotNone(latest_data)
        self.assertIsNotNone(history)
        self.assertTrue(len(sensor_handler.SENSOR_HISTORY) > 0) # History should now be populated
        self.assertEqual(latest_data, sensor_handler.SENSOR_HISTORY[-1])


    def test_generate_and_add_new_reading(self):
        """Test generating and adding a new reading."""
        sensor_handler.initialize_history() # Populate history
        initial_length = len(sensor_handler.SENSOR_HISTORY)
        
        new_data_point = sensor_handler.generate_and_add_new_reading()
        
        self.assertIsNotNone(new_data_point)
        self.assertIn("timestamp", new_data_point)
        self.assertEqual(len(sensor_handler.SENSOR_HISTORY), initial_length + 1)
        self.assertEqual(sensor_handler.SENSOR_HISTORY[-1], new_data_point)

        # Check if timestamp is later
        if initial_length > 0:
            last_time_before_add = datetime.strptime(sensor_handler.SENSOR_HISTORY[-2]["timestamp"], "%Y-%m-%d %H:%M:%S")
            new_time = datetime.strptime(new_data_point["timestamp"], "%Y-%m-%d %H:%M:%S")
            self.assertTrue(new_time > last_time_before_add)

    def test_generate_and_add_new_reading_initializes_if_empty(self):
        """Test that generate_and_add_new_reading initializes SENSOR_HISTORY if it's empty."""
        self.assertEqual(len(sensor_handler.SENSOR_HISTORY), 0) # Should be empty
        
        new_data_point = sensor_handler.generate_and_add_new_reading()
        
        self.assertIsNotNone(new_data_point)
        # After initializing and adding one point, length should be > 1 (initial history + 1 new)
        # or exactly 1 if initialize_history somehow failed to populate (which other tests check)
        # Given initialize_history creates ~2016 entries, this should be ~2017
        self.assertTrue(len(sensor_handler.SENSOR_HISTORY) > 1) 
        self.assertEqual(sensor_handler.SENSOR_HISTORY[-1], new_data_point)

if __name__ == '__main__':
    unittest.main()
