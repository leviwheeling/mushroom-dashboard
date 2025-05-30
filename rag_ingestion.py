import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from datetime import datetime, timedelta
import os
import time
import requests # For Ollama API calls
import json

try:
    from sensor_handler import generate_pseudo_sensor_data
except ImportError:
    print("Error: sensor_handler.py not found. Please ensure it's in the same directory.")
    exit()

# --- Configuration ---
ZONE_NAMES = ["Babylon 1", "Babylon 2", "Mine", "Tent 1", "Tent 2", "Bear Mountain"]
CHROMA_DB_PATH = "chroma_db_data"
COLLECTION_NAME = "mushroom_zone_data"
OLLAMA_EMBED_MODEL = 'nomic-embed-text'
OLLAMA_API_URL = 'http://localhost:11434/api/embeddings'

# --- Custom Ollama Embedding Function ---
class OllamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str, api_url: str):
        self.model_name = model_name
        self.api_url = api_url
        self._test_ollama_connection()

    def _test_ollama_connection(self):
        print(f"Testing connection to Ollama and model '{self.model_name}'...")
        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model_name, "prompt": "test"},
                timeout=5 # 5 seconds timeout
            )
            response.raise_for_status() # Raise an exception for HTTP errors
            print("Ollama connection and model access successful.")
            return True
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Could not connect to Ollama at {self.api_url}. Please ensure Ollama is running.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"ERROR: Ollama model '{self.model_name}' not found. Please run 'ollama pull {self.model_name}'.")
            else:
                print(f"ERROR: HTTP error connecting to Ollama: {e}")
        except requests.exceptions.Timeout:
            print(f"ERROR: Timeout connecting to Ollama at {self.api_url}.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while testing Ollama connection: {e}")
        
        print("WARNING: Proceeding without successful Ollama connection. Embeddings will likely fail.")
        return False

    def __call__(self, texts: Documents) -> Embeddings:
        embeddings_list = []
        for i, text_input in enumerate(texts):
            try:
                response = requests.post(
                    self.api_url,
                    json={"model": self.model_name, "prompt": text_input}
                )
                response.raise_for_status()
                response_json = response.json()
                
                if "embedding" not in response_json:
                    raise ValueError("Ollama API response does not contain 'embedding' key.")
                
                embeddings_list.append(response_json["embedding"])
                # Optional: Add a small delay to avoid overwhelming Ollama, though usually not needed for local.
                # if (i + 1) % 10 == 0: # e.g., every 10 embeddings
                #     print(f"Generated {i+1}/{len(texts)} embeddings...")
                #     time.sleep(0.1)

            except requests.exceptions.ConnectionError as e:
                print(f"CRITICAL: Could not connect to Ollama at {self.api_url} during embedding generation. Halting. Error: {e}")
                raise # Re-raise to stop the process if Ollama is down
            except requests.exceptions.HTTPError as e:
                error_message = f"CRITICAL: HTTP error from Ollama during embedding: {e}."
                if e.response is not None:
                    try:
                        error_detail = e.response.json().get('error', 'No additional error detail.')
                        error_message += f" Detail: {error_detail}"
                    except json.JSONDecodeError:
                        error_message += f" Raw response: {e.response.text}"
                print(error_message)
                raise 
            except ValueError as e:
                print(f"CRITICAL: Error processing Ollama response for text '{text_input[:50]}...': {e}")
                raise
            except Exception as e:
                print(f"CRITICAL: An unexpected error occurred during embedding generation for text '{text_input[:50]}...': {e}")
                raise
        return embeddings_list

# --- Main Ingestion Logic ---
def main():
    print("Initializing ChromaDB...")
    try:
        if not os.path.exists(CHROMA_DB_PATH):
            os.makedirs(CHROMA_DB_PATH)
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    except Exception as e:
        print(f"Error initializing ChromaDB: {e}")
        return

    print(f"Initializing Ollama Embedding Function with model: {OLLAMA_EMBED_MODEL}")
    try:
        ollama_ef = OllamaEmbeddingFunction(model_name=OLLAMA_EMBED_MODEL, api_url=OLLAMA_API_URL)
    except Exception as e: # Should catch issues from _test_ollama_connection if they are severe
        print(f"Could not initialize OllamaEmbeddingFunction: {e}. Aborting.")
        return
        
    # Check if collection exists and delete it to ensure new embedding function is used
    # This is important if you change the embedding function for an existing collection name
    try:
        existing_collections = [col.name for col in client.list_collections()]
        if COLLECTION_NAME in existing_collections:
            print(f"Collection '{COLLECTION_NAME}' exists. Deleting it to apply new embedding function...")
            client.delete_collection(name=COLLECTION_NAME)
            print(f"Collection '{COLLECTION_NAME}' deleted.")
    except Exception as e:
        print(f"Error during pre-check/deletion of existing collection: {e}")
        # Decide if this is critical enough to stop. For now, we'll try to proceed.

    print(f"Getting or creating collection: {COLLECTION_NAME}")
    try:
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ollama_ef,
            metadata={"hnsw:space": "cosine"} # Example metadata, adjust as needed
        )
    except Exception as e:
        print(f"Error getting or creating collection with Ollama embeddings: {e}")
        return

    print("Starting data generation and ingestion...")
    start_time_overall = datetime.now()

    for zone_name in ZONE_NAMES:
        print(f"\nProcessing zone: {zone_name}...")
        
        documents = []
        metadatas = []
        ids = []
        
        num_days = 7
        readings_per_day = 4 
        current_time = datetime.now() - timedelta(days=num_days) 

        for day in range(num_days):
            for i in range(readings_per_day):
                reading_time = current_time + timedelta(days=day, hours=i*6)
                sensor_reading = generate_pseudo_sensor_data(base_time=reading_time)
                data_timestamp_str = sensor_reading["timestamp"]
                
                document_text = (
                    f"Sensor reading for Zone '{zone_name}' at {data_timestamp_str}: "
                    f"Temperature {sensor_reading['temperature']:.1f}°F, "
                    f"Humidity {sensor_reading['humidity']:.1f}%, "
                    f"CO2 {sensor_reading['CO2']} ppm."
                )
                documents.append(document_text)
                
                metadatas.append({
                    "zone": zone_name,
                    "timestamp": data_timestamp_str,
                    "original_temperature": float(sensor_reading['temperature']),
                    "original_humidity": float(sensor_reading['humidity']),
                    "original_co2": int(sensor_reading['CO2'])
                })
                
                safe_zone_name = zone_name.replace(' ', '_')
                ids.append(f"{safe_zone_name}_{data_timestamp_str.replace(' ', '_').replace(':', '-')}")

        if documents:
            print(f"Adding {len(documents)} documents to ChromaDB for zone '{zone_name}' using Ollama embeddings...")
            try:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Data ingestion complete for zone: {zone_name}.")
            except Exception as e:
                print(f"Error adding documents to ChromaDB for zone '{zone_name}': {e}")
                print("Skipping this zone due to embedding/DB error.")
        else:
            print(f"No documents generated for zone: {zone_name}.")

    end_time_overall = datetime.now()
    print(f"\nAll data ingestion processes finished in {end_time_overall - start_time_overall}.")
    
    try:
        final_count = collection.count()
        print(f"Total documents in collection '{COLLECTION_NAME}': {final_count}")
    except Exception as e:
        print(f"Error retrieving final collection count: {e}")

if __name__ == "__main__":
    main()
