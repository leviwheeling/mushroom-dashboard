import unittest
from unittest.mock import patch, mock_open
import os # Used to manipulate environment variables if needed, though not for this task

# Add project root to sys.path to allow importing app_config
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app_config

class TestAppConfig(unittest.TestCase):

    @patch('builtins.open', side_effect=FileNotFoundError("key.txt not found"))
    def test_load_api_key_file_not_found(self, mock_file):
        """Test that FileNotFoundError is raised if key.txt is not found."""
        with self.assertRaises(FileNotFoundError) as context:
            app_config.load_api_key()
        self.assertIn("key.txt not found", str(context.exception))

    @patch('builtins.open', new_callable=mock_open, read_data="")
    def test_load_api_key_empty_key(self, mock_file):
        """Test that ValueError is raised if the API key in key.txt is empty."""
        with self.assertRaises(ValueError) as context:
            app_config.load_api_key()
        self.assertIn("API key is empty", str(context.exception))

    @patch('builtins.open', new_callable=mock_open, read_data="test_api_key_123")
    def test_load_api_key_valid_key(self, mock_file):
        """Test that a valid API key is read and returned correctly."""
        api_key = app_config.load_api_key()
        self.assertEqual(api_key, "test_api_key_123")

    @patch('builtins.open', new_callable=mock_open, read_data="  test_api_key_with_spaces  ")
    def test_load_api_key_valid_key_with_spaces(self, mock_file):
        """Test that a valid API key with leading/trailing spaces is stripped."""
        api_key = app_config.load_api_key()
        self.assertEqual(api_key, "test_api_key_with_spaces")
        
    # It is complex to directly test OPENAI_CLIENT initialization without
    # a real API key or extensive mocking of the OpenAI library itself.
    # The tests above cover the load_api_key logic which is the core
    # configurable part of app_config.py.

    # We also need to consider that app_config.py executes load_api_key() at module level.
    # To test different scenarios for load_api_key(), we might need to reload the module
    # or structure app_config.py differently (e.g., make API_KEY and OPENAI_CLIENT load lazily).
    # For now, these tests assume load_api_key() can be called independently.
    # If running all tests in sequence causes issues due to module-level execution,
    # further adjustments or using `importlib.reload` might be needed.

if __name__ == '__main__':
    unittest.main()
