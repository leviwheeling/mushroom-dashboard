import os
import json
import requests
import chromadb
from datetime import datetime
import uuid

# Import the custom embedding function
try:
    from ollama_utils import OllamaEmbeddingFunction
except ImportError:
    print("Error: ollama_utils.py not found. Please ensure it's in the same directory.")
    class OllamaEmbeddingFunction: # type: ignore
        def __init__(self, *args, **kwargs): print("Dummy OllamaEmbeddingFunction used due to import error.")
        def __call__(self, texts): raise NotImplementedError("Dummy EF called")

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED_API_URL = "http://localhost:11434/api/embeddings"
OLLAMA_LLM_MODEL = "mushroom_gemma"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
CHROMA_DB_PATH = "chroma_db_data"
COLLECTION_NAME = "mushroom_zone_data"
CONVERSATION_HISTORY_DIR = "conversation_history"

os.makedirs(CONVERSATION_HISTORY_DIR, exist_ok=True)

# --- ChromaDB and Embedding Function Initialization ---
rag_collection = None
ollama_embed_ef = None
chroma_client = None

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    ollama_embed_ef = OllamaEmbeddingFunction(model_name=OLLAMA_EMBED_MODEL, api_url=OLLAMA_EMBED_API_URL)
    try:
        rag_collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=ollama_embed_ef # This is important for ChromaDB to use our function
        )
        print(f"Successfully connected to ChromaDB and retrieved collection '{COLLECTION_NAME}'.")
        print(f"ChromaDB collection count: {rag_collection.count()}")
    except Exception as e: 
        print(f"Info: Collection '{COLLECTION_NAME}' not found or EF incompatible ({e}). Will attempt to get/create later if needed by RAG.")
except Exception as e:
    print(f"Error initializing ChromaDB or OllamaEmbeddingFunction: {e}. RAG capabilities will be affected.")

# --- Conversation History Management ---
def load_conversation_history(thread_id: str) -> list:
    history_file = os.path.join(CONVERSATION_HISTORY_DIR, f"{thread_id}.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {history_file}. Starting with empty history.")
            return []
    return []

def save_conversation_history(thread_id: str, history: list):
    history_file = os.path.join(CONVERSATION_HISTORY_DIR, f"{thread_id}.json")
    try:
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        print(f"Error saving conversation history to {history_file}: {e}")

# --- Core AI Functions ---
def start_conversation() -> str:
    thread_id = uuid.uuid4().hex
    save_conversation_history(thread_id, []) 
    print(f"New conversation started with Thread ID: {thread_id}")
    return thread_id

def send_message(thread_id: str, user_message: str, zone_name: str) -> str:
    global rag_collection 
    global ollama_embed_ef
    global chroma_client 

    context_str = "No RAG context available." 

    if ollama_embed_ef is None:
        print("CRITICAL Error: Ollama Embedding Function not initialized. Cannot perform RAG.")
        try:
            ollama_embed_ef = OllamaEmbeddingFunction(model_name=OLLAMA_EMBED_MODEL, api_url=OLLAMA_EMBED_API_URL)
            print("Re-initialized OllamaEmbeddingFunction in send_message.")
        except Exception as e_ef:
            print(f"Failed to re-initialize OllamaEmbeddingFunction in send_message: {e_ef}")
            return "Error: AI system's embedding function is not working."
    
    if chroma_client is None:
        print("CRITICAL Error: Chroma client not initialized. Cannot perform RAG.")
        try:
            chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            print("Re-initialized ChromaDB client in send_message.")
        except Exception as e_chroma:
            print(f"Failed to re-initialize ChromaDB client in send_message: {e_chroma}")
            return "Error: AI system's database connection is not working."

    if rag_collection is None:
        print(f"Warning: RAG collection '{COLLECTION_NAME}' not available at start of send_message. Attempting to get/re-initialize.")
        if chroma_client and ollama_embed_ef:
            try:
                rag_collection = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=ollama_embed_ef)
                print(f"Successfully got collection '{COLLECTION_NAME}' within send_message. Count: {rag_collection.count()}")
            except Exception as e_coll:
                print(f"Error: Failed to get RAG collection '{COLLECTION_NAME}' within send_message: {e_coll}.")
                context_str = "No RAG context available (collection access failed)."
        else:
            print("Error: Chroma client or embedding function still not available. Cannot access RAG collection.")
            context_str = "No RAG context available (Chroma client or EF not initialized)."
    
    if rag_collection and ollama_embed_ef:
        print(f"Retrieving RAG context for Zone: {zone_name} based on message: '{user_message[:50]}...'")
        try:
            message_embedding = ollama_embed_ef([user_message])[0]
            results = rag_collection.query(
                query_embeddings=[message_embedding],
                n_results=3,
                where={"zone": zone_name} 
            )
            retrieved_docs_texts = results.get('documents', [[]])[0]
            if retrieved_docs_texts:
                context_str = "\n--- Context --- \n".join(retrieved_docs_texts) 
                print(f"Retrieved {len(retrieved_docs_texts)} documents from RAG.")
            else:
                context_str = "No relevant historical data found for this query in the specified zone."
                print("No documents found in RAG for the current query and zone.")
        except Exception as e_rag:
            print(f"Error during RAG retrieval: {e_rag}")
            context_str = "Error retrieving RAG context."
    
    history = load_conversation_history(thread_id)
    history.append({"role": "user", "content": user_message})

    formatted_history = ""
    for entry in history[-5:]: 
        role = entry.get('role', 'Unknown')
        content = entry.get('content', '')
        formatted_history += f"{role.capitalize()}: {content}\n"

    prompt = f"""You are assisting with Zone: {zone_name}.

Retrieved context from historical data for Zone {zone_name}:
{context_str}

Conversation History (last few messages):
{formatted_history}
User: {user_message}
Assistant:"""

    print(f"\n--- Constructed Prompt for Ollama ({OLLAMA_LLM_MODEL}) ---")
    print(f"Prompt context length: ~{len(context_str)} chars, History length: ~{len(formatted_history)} chars.")
    print("--- End of Prompt ---")

    ai_response_text = "Error: Could not get a response from Ollama."
    try:
        print(f"Sending prompt to Ollama model: {OLLAMA_LLM_MODEL}...")
        ollama_payload = {
            "model": OLLAMA_LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": { 
                "temperature": 0.7, 
                "top_k": 50 
            }
        }
        response = requests.post(OLLAMA_API_URL, json=ollama_payload, timeout=60) 
        response.raise_for_status() 
        
        response_json = response.json()
        ai_response_text = response_json.get("response", "Error: No 'response' key in Ollama output.").strip()
        
    except requests.exceptions.ConnectionError as e:
        ai_response_text = f"Error: Could not connect to Ollama at {OLLAMA_API_URL}. Is Ollama running? ({e})"
        print(ai_response_text) 
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text
        try:
            error_json = e.response.json()
            error_detail = error_json.get('error', error_detail) 
            if "model not found" in error_detail.lower() or (e.response.status_code == 404 and "no such file" in error_detail.lower()): 
                 ai_response_text = f"Error: Ollama LLM model '{OLLAMA_LLM_MODEL}' not found. Please ensure it is created/pulled. (Details: {error_detail})"
            else:
                ai_response_text = f"Error: HTTP error from Ollama: {e.response.status_code} (Details: {error_detail})"
        except json.JSONDecodeError: 
            ai_response_text = f"Error: HTTP error from Ollama: {e.response.status_code}. Could not decode error response. (Raw response: {error_detail})"
        print(ai_response_text) 
    except requests.exceptions.Timeout:
        ai_response_text = f"Error: Timeout connecting to Ollama at {OLLAMA_API_URL} for generation."
        print(ai_response_text) 
    except Exception as e: 
        ai_response_text = f"An unexpected error occurred while communicating with Ollama: {e}"
        print(ai_response_text) 
    
    print(f"AI Raw Response (first 100 chars): {ai_response_text[:100]}...")

    history.append({"role": "assistant", "content": ai_response_text})
    save_conversation_history(thread_id, history)

    return ai_response_text

if __name__ == "__main__":
    print("Starting AI Model script (Ollama & RAG integration)...")
    
    if ollama_embed_ef is None: 
        print("Critical Error: Ollama Embedding Function failed to initialize globally. Check Ollama service and nomic-embed-text model. Exiting test.")
        exit()
    
    if rag_collection is None :
         print("Warning: RAG collection was not available on startup. RAG queries will be skipped if it cannot be accessed later.")
         print(f"Ensure that rag_ingestion.py has been run and the collection '{COLLECTION_NAME}' exists in '{CHROMA_DB_PATH}'.")
    
    thread_id = start_conversation()
    zone_to_query = "Babylon 1" 
    
    print(f"\n--- Querying for Zone: {zone_to_query} ---")
    user_q1 = "What were the CO2 levels like yesterday and are there any anomalies?"
    print(f"\nUser: {user_q1}")
    response1 = send_message(thread_id, user_q1, zone_name=zone_to_query)
    print(f"\nAI Assistant: {response1}")

    user_q2 = "Based on that, what should I check or do?"
    print(f"\nUser: {user_q2}")
    response2 = send_message(thread_id, user_q2, zone_name=zone_to_query) 
    print(f"\nAI Assistant: {response2}")

    zone_to_query_2 = "Mine" 
    print(f"\n--- Querying for Zone: {zone_to_query_2} ---")
    user_q3 = "Any temperature alerts for the Mine recently?"
    print(f"\nUser: {user_q3}")
    response3 = send_message(thread_id, user_q3, zone_name=zone_to_query_2)
    print(f"\nAI Assistant: {response3}")
    
    user_q4 = "How do I generally improve mushroom yield?"
    print(f"\nUser: {user_q4}")
    response4 = send_message(thread_id, user_q4, zone_name="General") 
    print(f"\nAI Assistant: {response4}")

    print("\n--- Example Conversation End ---")
    print(f"Conversation history for this session is stored in: {CONVERSATION_HISTORY_DIR}/{thread_id}.json")
