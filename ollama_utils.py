import requests
import json
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings # Ensure these are the correct imports for ChromaDB types

class OllamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str, api_url: str):
        self.model_name = model_name
        self.api_url = api_url
        # No initial test here to allow script to run even if Ollama is temporarily down.
        # Tests will occur during actual calls.

    def __call__(self, texts: Documents) -> Embeddings:
        all_embeddings = []
        for i, text_input in enumerate(texts):
            try:
                payload = {"model": self.model_name, "prompt": text_input}
                response = requests.post(self.api_url, json=payload, timeout=10) # 10s timeout
                response.raise_for_status()
                response_json = response.json()
                if "embedding" in response_json:
                    all_embeddings.append(response_json["embedding"])
                else:
                    print(f"Warning: Embedding not found in response for document {i+1}/{len(texts)} ('{text_input[:50]}...'). Raising error.")
                    raise ValueError(f"Embedding not found for document: {text_input[:50]}...")
            except requests.exceptions.ConnectionError as e:
                print(f"CRITICAL: Could not connect to Ollama at {self.api_url} for embeddings. Is Ollama running? Error: {e}")
                raise
            except requests.exceptions.HTTPError as e:
                error_message = f"CRITICAL: HTTP error from Ollama (embeddings) for model '{self.model_name}': {e}."
                if e.response is not None:
                    try:
                        error_detail = e.response.json().get('error', 'No additional error detail.')
                        error_message += f" Detail: {error_detail}"
                        if "model not found" in error_detail.lower(): # Specific check for model not found
                             print(f"CRITICAL: Ollama embedding model '{self.model_name}' not found. Please run 'ollama pull {self.model_name}'.")
                    except json.JSONDecodeError:
                        error_message += f" Raw response: {e.response.text}"
                print(error_message)
                raise
            except requests.exceptions.Timeout:
                print(f"CRITICAL: Timeout connecting to Ollama at {self.api_url} for embeddings.")
                raise
            except ValueError as e: # Catch custom ValueError
                print(f"CRITICAL: Error processing Ollama response for text '{text_input[:50]}...': {e}")
                raise
            except Exception as e:
                print(f"CRITICAL: An unexpected error occurred during embedding generation for text '{text_input[:50]}...': {e}")
                raise
        
        if len(all_embeddings) != len(texts):
            # This should ideally be caught by errors raised above
            raise ValueError(f"Failed to generate embeddings for all texts. Expected {len(texts)}, got {len(all_embeddings)}.")
        return all_embeddings
