import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration for embedding model
EMBEDDINGS_URL = os.getenv("GRANITE_EMBEDDINGS_URL")
EMBEDDINGS_API = os.getenv("GRANITE_EMBEDDINGS_API")
EMBEDDINGS_MODEL_NAME = os.getenv("GRANITE_EMBEDDINGS_MODEL_NAME")
EMBEDDINGS_TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", 512))  # Default to 512 if TOKEN_LIMIT is not set

# Ensure all required environment variables are set
if not (EMBEDDINGS_URL and EMBEDDINGS_API and EMBEDDINGS_MODEL_NAME):
    raise EnvironmentError("Missing required environment variables for embedding model.")

# Tokenizer configuration (adjust based on your model)
try:
    import tiktoken
    TOKENIZER = tiktoken.get_encoding("cl100k_base")  # Example for OpenAI tokenizer
except ImportError:
    TOKENIZER = None
    print("Tokenizer library not installed. Install 'tiktoken' if using OpenAI models.")

def load_processed_json(filepath):
    """Load processed JSON data from a file."""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_embeddings(filepath, data):
    """Save embeddings data to a file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        print(f"Embeddings successfully saved to {filepath}")
    except Exception as e:
        print(f"Failed to save embeddings to {filepath}: {str(e)}")


def chunk_content(content, token_limit):
    """Chunk content into smaller pieces based on token limit."""
    if TOKENIZER is None:
        raise RuntimeError("Tokenizer not configured. Install and configure a tokenizer.")

    tokens = TOKENIZER.encode(content)
    chunks = []

    while tokens:
        chunk = tokens[:token_limit]
        chunks.append(chunk)
        tokens = tokens[token_limit:]

    if any(len(chunk) > token_limit for chunk in chunks):
        print("Warning: Some chunks still exceed the token limit after initial splitting.")

    return [TOKENIZER.decode(chunk) for chunk in chunks]


def generate_embeddings(content):
    """Generate embeddings for a given content using the Granite Embedding API."""
    headers = {
        "Authorization": f"Bearer {EMBEDDINGS_API}",
        "Content-Type": "application/json"
    }

    if len(TOKENIZER.encode(content)) > EMBEDDINGS_TOKEN_LIMIT:
        print("Content exceeds token limit, chunking...")
        chunks = chunk_content(content, EMBEDDINGS_TOKEN_LIMIT)
    else:
        chunks = [content]

    embeddings = []

    for chunk in chunks:
        success = False
        retries = 3
        while not success and retries > 0:
            payload = {
                "model": EMBEDDINGS_MODEL_NAME,
                "input": chunk
            }
            response = requests.post(EMBEDDINGS_URL, headers=headers, json=payload)

            if response.status_code == 200:
                response_data = response.json()
                if "embedding" in response_data.get("data", [{}])[0]:
                    embeddings.append(response_data["data"][0]["embedding"])
                    success = True
                    print("Successfully processed a chunk.")
                else:
                    print("Error: Response missing 'embedding' field:", json.dumps(response_data))
                    retries -= 1
            else:
                print(f"Error: Failed to generate embeddings (Attempt {3 - retries + 1}): {response.status_code} {response.text}")
                retries -= 1

            if not success and retries == 0:
                print("Failed to process a chunk after retries. Rechunking...")
                chunk_tokens = TOKENIZER.encode(chunk)
                if len(chunk_tokens) > 10:  # Avoid infinite loop by ensuring tokens can be split further
                    chunk = TOKENIZER.decode(chunk_tokens[:len(chunk_tokens) // 2])
                    chunks.append(chunk)

    # Combine embeddings if multiple chunks were processed
    if len(embeddings) > 1:
        return embeddings  # Return as a list of embeddings for each chunk
    return embeddings[0] if embeddings else None


def process_single_file(input_filepath, output_filepath):
    """Process a single file to generate embeddings and save the output."""
    data = load_processed_json(input_filepath)
    content = data.get("content", "")

    if not content:
        print(f"No content found in {input_filepath}, skipping.")
        return

    try:
        embeddings = generate_embeddings(content)
        if embeddings:
            data["embedding"] = embeddings
            save_embeddings(output_filepath, data)
            print(f"Generated embeddings and saved: {output_filepath}")
        else:
            print(f"Error: No embeddings generated for {input_filepath}.")
    except Exception as e:
        print(f"Error processing {input_filepath}: {str(e)}")


if __name__ == "__main__":
    input_filepath = "docs/processed/langchain/agents_processed.json"
    output_filepath = "docs/embeddings/langchain/agents_embeddings.txt"

    process_single_file(input_filepath, output_filepath)
