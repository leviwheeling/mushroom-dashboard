import os
from openai import OpenAI

def load_api_key():
    """
    Reads the API key from a file named "key.txt".

    Raises:
        FileNotFoundError: If "key.txt" is not found.
        ValueError: If the key is empty.
        Exception: For other I/O errors.

    Returns:
        str: The API key.
    """
    try:
        with open("key.txt", "r") as f:
            api_key = f.read().strip()
        if not api_key:
            raise ValueError("API key is empty. Please ensure 'key.txt' contains a valid key.")
        return api_key
    except FileNotFoundError:
        raise FileNotFoundError("key.txt not found. Please create it and add your OpenAI API key.")
    except IOError:
        raise Exception("Error reading API key from key.txt")

API_KEY = load_api_key()
OPENAI_CLIENT = OpenAI(api_key=API_KEY)

def get_openai_client():
    """
    Returns the initialized OpenAI client.

    Returns:
        openai.OpenAI: The OpenAI client instance.
    """
    return OPENAI_CLIENT

def get_api_key():
    """
    Returns the API key.

    Returns:
        str: The API key.
    """
    return API_KEY
