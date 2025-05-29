import sys
from app_config import get_openai_client

try:
    CLIENT = get_openai_client()
    models = CLIENT.models.list()
    print("Available models:")
    for model in models:
        print(model.id)
except FileNotFoundError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: An unexpected error occurred: {e}")
    sys.exit(1)