from openai import OpenAI

def get_api_key():
    try:
        with open('key.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception("key.txt not found. Please create it from key.template.txt")

client = OpenAI(api_key=get_api_key())

try:
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(model.id)
except Exception as e:
    print(f"Error: {e}")