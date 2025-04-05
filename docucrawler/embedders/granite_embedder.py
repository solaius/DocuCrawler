"""
Granite embedder implementation for generating document embeddings.
"""

import os
import asyncio
import requests
from typing import Dict, Any, List, Union, Optional
import tiktoken

from docucrawler.embedders.base import BaseEmbedder
from docucrawler.utils.common import (
    ensure_directory_exists, log_memory_usage, load_json, save_json
)


class GraniteEmbedder(BaseEmbedder):
    """Embedder implementation using Granite embedding models."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Granite embedder.
        
        Args:
            config: Dictionary containing embedder configuration
        """
        super().__init__(config)
        self.api_url = config.get('api_url')
        self.api_key = config.get('api_key')
        self.model_name = config.get('model_name')
        self.token_limit = config.get('token_limit', 512)
        self.max_concurrent = config.get('max_concurrent', 10)
        self.max_retries = config.get('max_retries', 3)
        
        # Initialize tokenizer
        self.tokenizer = None
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Failed to initialize tokenizer: {e}")
            print("Falling back to approximate token counting.")
    
    def chunk_content(self, content: str, token_limit: Optional[int] = None) -> List[str]:
        """Chunk content into smaller pieces based on token limit.
        
        Args:
            content: Content to chunk
            token_limit: Maximum number of tokens per chunk (defaults to self.token_limit)
            
        Returns:
            List of content chunks
        """
        if token_limit is None:
            token_limit = self.token_limit
        
        if self.tokenizer is None:
            # Fallback to approximate token counting (assuming ~4 chars per token)
            approx_tokens = len(content) // 4
            if approx_tokens <= token_limit:
                return [content]
            
            # Split by paragraphs first
            paragraphs = content.split('\n\n')
            chunks = []
            current_chunk = ""
            current_tokens = 0
            
            for para in paragraphs:
                para_tokens = len(para) // 4
                if current_tokens + para_tokens <= token_limit:
                    current_chunk += para + '\n\n'
                    current_tokens += para_tokens
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    # If paragraph is too long, split it further
                    if para_tokens > token_limit:
                        words = para.split()
                        current_chunk = ""
                        current_tokens = 0
                        
                        for word in words:
                            word_tokens = len(word) // 4 + 1  # +1 for space
                            if current_tokens + word_tokens <= token_limit:
                                current_chunk += word + ' '
                                current_tokens += word_tokens
                            else:
                                chunks.append(current_chunk.strip())
                                current_chunk = word + ' '
                                current_tokens = word_tokens
                    else:
                        current_chunk = para + '\n\n'
                        current_tokens = para_tokens
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        else:
            # Use the tokenizer for accurate token counting
            tokens = self.tokenizer.encode(content)
            
            if len(tokens) <= token_limit:
                return [content]
            
            chunks = []
            for i in range(0, len(tokens), token_limit):
                chunk_tokens = tokens[i:i + token_limit]
                chunks.append(self.tokenizer.decode(chunk_tokens))
            
            return chunks
    
    def embed_document(self, content: str) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for a single document.
        
        Args:
            content: Document content to embed
            
        Returns:
            Document embeddings as a list of floats or list of list of floats (for chunked content)
        """
        # Check if content needs to be chunked
        if self.tokenizer:
            content_tokens = len(self.tokenizer.encode(content))
            needs_chunking = content_tokens > self.token_limit
        else:
            # Approximate token count
            needs_chunking = len(content) // 4 > self.token_limit
        
        if needs_chunking:
            print(f"Content exceeds token limit ({self.token_limit}), chunking...")
            chunks = self.chunk_content(content)
            return [self._generate_embedding_for_chunk(chunk) for chunk in chunks]
        else:
            return self._generate_embedding_for_chunk(content)
    
    def _generate_embedding_for_chunk(self, chunk: str) -> List[float]:
        """Generate embedding for a single chunk of content.
        
        Args:
            chunk: Content chunk to embed
            
        Returns:
            Embedding as a list of floats
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "input": chunk
                }
                
                response = requests.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                
                response_data = response.json()
                
                # Check if the response has the expected structure
                if "data" in response_data and len(response_data["data"]) > 0:
                    if "embedding" in response_data["data"][0]:
                        return response_data["data"][0]["embedding"]
                
                print(f"Unexpected response format: {response_data}")
                
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
        
        raise Exception(f"Failed to generate embedding after {self.max_retries} attempts")
    
    async def generate_embeddings(self, input_dir: str, output_dir: str) -> List[str]:
        """Generate embeddings for documents in the input directory and save to output directory.
        
        Args:
            input_dir: Directory containing documents to embed
            output_dir: Directory to save documents with embeddings
            
        Returns:
            List of paths to files with embeddings
        """
        ensure_directory_exists(output_dir)
        embedded_files = []
        
        # Get all JSON files in the input directory
        files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
        
        for i in range(0, len(files), self.max_concurrent):
            batch = files[i:i + self.max_concurrent]
            log_memory_usage(prefix=f"Before embedding batch {i // self.max_concurrent + 1}: ")
            
            # Create a new list of tasks for the current batch
            tasks = [
                asyncio.to_thread(
                    self._embed_and_save_document,
                    os.path.join(input_dir, filename),
                    os.path.join(output_dir, filename.replace('.json', '_embedded.json'))
                )
                for filename in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            embedded_files.extend([path for path in batch_results if path])
            
            log_memory_usage(prefix=f"After embedding batch {i // self.max_concurrent + 1}: ")
        
        return embedded_files
    
    def _embed_and_save_document(self, input_filepath: str, output_filepath: str) -> str:
        """Generate embeddings for a document and save the output.
        
        Args:
            input_filepath: Path to the input document
            output_filepath: Path to save the document with embeddings
            
        Returns:
            Path to the document with embeddings or empty string if embedding failed
        """
        try:
            data = load_json(input_filepath)
            content = data.get("content", "")
            
            if not content:
                print(f"No content found in {input_filepath}, skipping.")
                return ""
            
            embeddings = self.embed_document(content)
            data["embedding"] = embeddings
            
            save_json(output_filepath, data)
            print(f"Generated embeddings and saved: {output_filepath}")
            return output_filepath
        except Exception as e:
            print(f"Error embedding {input_filepath}: {e}")
            return ""