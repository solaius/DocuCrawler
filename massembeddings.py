import os
import json
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration for embedding model
EMBEDDINGS_URL = os.getenv("GRANITE_EMBEDDINGS_URL")
EMBEDDINGS_API = os.getenv("GRANITE_EMBEDDINGS_API")
EMBEDDINGS_MODEL_NAME = os.getenv("GRANITE_EMBEDDINGS_MODEL_NAME")

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

TOKEN_LIMIT = 512  # Adjust this based on your model's token limit

def ensure_directory_exists(directory):
    """Ensure a directory exists."""
    os.makedirs(directory, exist_ok=True)

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
    while True:
        chunks = [tokens[i:i + token_limit] for i in range(0, len(tokens), token_limit)]
        if all(len(chunk) <= token_limit for chunk in chunks):
            break
        token_limit -= 10  # Reduce the token limit slightly and retry

    return [TOKENIZER.decode(chunk) for chunk in chunks]

def generate_embeddings(content):
    """Generate embeddings for a given content using the Granite Embedding API."""
    headers = {
        "Authorization": f"Bearer {EMBEDDINGS_API}",
        "Content-Type": "application/json"
    }

    if len(TOKENIZER.encode(content)) > TOKEN_LIMIT:
        print("Content exceeds token limit, chunking...")
        chunks = chunk_content(content, TOKEN_LIMIT)
    else:
        chunks = [content]

    embeddings = []

    for chunk in chunks:
        payload = {
            "model": EMBEDDINGS_MODEL_NAME,
            "input": chunk
        }
        response = requests.post(EMBEDDINGS_URL, headers=headers, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            if "embedding" in response_data:
                embeddings.append(response_data["embedding"])
            else:
                print("Error: Response missing 'embedding' field:", json.dumps(response_data))
        else:
            print(f"Error: Failed to generate embeddings: {response.status_code} {response.text}")

    # Combine embeddings if multiple chunks were processed
    if len(embeddings) > 1:
        return embeddings  # Return as a list of embeddings for each chunk
    return embeddings[0] if embeddings else None

def process_file_for_embeddings(input_filepath, output_filepath):
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

async def process_files_in_parallel(input_dir, output_dir, max_concurrent=10):
    """Generate embeddings for files in a directory in parallel."""
    ensure_directory_exists(output_dir)

    files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

    for i in range(0, len(files), max_concurrent):
        batch = files[i:i + max_concurrent]
        tasks = [
            asyncio.to_thread(
                process_file_for_embeddings,
                os.path.join(input_dir, filename),
                os.path.join(output_dir, filename.replace('.json', '_embedding.json'))
            )
            for filename in batch
        ]

        await asyncio.gather(*tasks)

async def main():
    base_dir = 'docs'
    input_dirs = {
        "langchain": os.path.join(base_dir, 'processed', 'langchain'),
        "docling": os.path.join(base_dir, 'processed', 'docling')
    }
    output_dirs = {
        "langchain": os.path.join(base_dir, 'embeddings', 'langchain'),
        "docling": os.path.join(base_dir, 'embeddings', 'docling')
    }

    for key in input_dirs:
        input_dir = input_dirs[key]
        output_dir = output_dirs[key]

        print(f"Generating embeddings for files in {input_dir}...")
        await process_files_in_parallel(input_dir, output_dir, max_concurrent=10)

if __name__ == "__main__":
    asyncio.run(main())
