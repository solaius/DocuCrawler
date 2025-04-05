import os
import json
import asyncio
import re
import psutil

def ensure_directory_exists(directory):
    """Ensure a directory exists."""
    os.makedirs(directory, exist_ok=True)

def log_memory_usage(prefix=""):
    """Log current and peak memory usage."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    current_memory = memory_info.rss // (1024 * 1024)  # Convert to MB
    print(f"{prefix} Current Memory Usage: {current_memory} MB")

def load_markdown(filepath):
    """Load markdown data from a file."""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def clean_markdown(content):
    """Clean and preprocess markdown content to remove non-essential elements."""
    # Remove Markdown links
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)
    # Remove images
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    # Remove repetitive patterns like "\n * \n" or "* - *"
    content = re.sub(r'(\n\s*[*-]+\s*)+', '\n', content)
    # Remove multiple punctuation marks
    content = re.sub(r'[.]{3,}', '.', content)
    # Replace sequences of asterisks or dashes
    content = re.sub(r'[*-]{2,}', '', content)
    # Remove excessive newlines
    content = re.sub(r'\n{2,}', '\n', content)
    # Trim whitespace
    return content.strip()

def process_document(filepath):
    """Process a single markdown document to extract valuable data."""
    content = load_markdown(filepath)
    cleaned_content = clean_markdown(content)
    title = cleaned_content.split('\n', 1)[0]  # Use the first line as title

    return {
        "title": title,
        "summary": cleaned_content[:200],  # Truncate to first 200 characters for summary
        "content": cleaned_content,
        "metadata": {
            "length": len(cleaned_content),
            "filepath": filepath
        }
    }

async def process_files_in_parallel(input_dir, output_dir, max_concurrent=10):
    """Process markdown files in a directory in parallel."""
    ensure_directory_exists(output_dir)

    files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]

    for i in range(0, len(files), max_concurrent):
        batch = files[i:i + max_concurrent]
        log_memory_usage(prefix=f"Before batch {i // max_concurrent + 1}: ")

        # Create a new list of tasks for the current batch
        tasks = [
            asyncio.to_thread(process_and_save_document,
                              os.path.join(input_dir, filename),
                              os.path.join(output_dir, filename.replace('.txt', '_processed.json')))
            for filename in batch
        ]

        await asyncio.gather(*tasks)

        log_memory_usage(prefix=f"After batch {i // max_concurrent + 1}: ")

def process_and_save_document(input_filepath, output_filepath):
    """Process a document and save the output."""
    processed_data = process_document(input_filepath)
    with open(output_filepath, 'w', encoding='utf-8') as file:
        json.dump(processed_data, file, indent=4)

async def main():
    base_dir = 'docs'
    input_dirs = {
        "langchain": os.path.join(base_dir, 'crawled', 'langchain'),
        "docling": os.path.join(base_dir, 'crawled', 'docling')
    }
    output_dirs = {
        "langchain": os.path.join(base_dir, 'processed', 'langchain'),
        "docling": os.path.join(base_dir, 'processed', 'docling')
    }

    for key in input_dirs:
        input_dir = input_dirs[key]
        output_dir = output_dirs[key]

        print(f"Processing files in {input_dir}...")
        await process_files_in_parallel(input_dir, output_dir, max_concurrent=10)

if __name__ == "__main__":
    asyncio.run(main())
