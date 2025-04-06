"""
Enhanced Granite embedder implementation with advanced chunking strategies.
"""

import os
import asyncio
import requests
from typing import Dict, Any, List, Union, Optional
import tiktoken

from docucrawler.embedders.base import BaseEmbedder
from docucrawler.processors.advanced_chunker import AdvancedChunker
from docucrawler.utils.common import (
    ensure_directory_exists, log_memory_usage, load_json, save_json
)


class EnhancedGraniteEmbedder(BaseEmbedder):
    """Enhanced embedder implementation using Granite embedding models with advanced chunking."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the enhanced Granite embedder.
        
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
        
        # Advanced chunking configuration
        self.use_advanced_chunking = config.get('use_advanced_chunking', True)
        
        # Initialize tokenizer
        self.tokenizer = None
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Failed to initialize tokenizer: {e}")
            print("Falling back to approximate token counting.")
        
        # Initialize advanced chunker
        chunker_config = {
            'max_chunk_size': self.token_limit,
            'min_chunk_size': self.token_limit // 4,  # 25% of max size
            'overlap': self.token_limit // 10,  # 10% overlap
            'respect_sections': True,
            'respect_paragraphs': True,
            'respect_sentences': True
        }
        self.chunker = AdvancedChunker(chunker_config)
    
    def chunk_content(self, content: str, token_limit: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Chunk content into smaller pieces based on token limit.
        
        Args:
            content: Content to chunk
            token_limit: Maximum number of tokens per chunk (defaults to self.token_limit)
            metadata: Optional metadata about the content
            
        Returns:
            List of content chunks
        """
        if token_limit is None:
            token_limit = self.token_limit
        
        if metadata is None:
            metadata = {}
        
        # Ensure we're not working with extremely large content
        if len(content) > 100000:  # 100K character limit as a safety measure
            print(f"Content is very large ({len(content)} chars), truncating to 100K chars")
            content = content[:100000]
        
        # Remove any potentially problematic characters
        content = content.replace('\x00', '')
        
        # Use a smaller token limit for safety
        safe_token_limit = min(token_limit, 400)  # Use 400 as a safer limit
        
        # Use advanced chunking if enabled
        if self.use_advanced_chunking:
            # Update chunker config with current token limit
            self.chunker.max_chunk_size = safe_token_limit
            self.chunker.min_chunk_size = safe_token_limit // 4
            self.chunker.overlap = safe_token_limit // 10
            
            # Get chunks using advanced chunker
            chunk_results = self.chunker.chunk_text(content, metadata)
            return [chunk['content'] for chunk in chunk_results]
        
        # Fall back to basic chunking if advanced chunking is disabled
        elif self.tokenizer is None:
            # Fallback to approximate token counting (assuming ~4 chars per token)
            char_limit = safe_token_limit * 4  # Approximate 4 chars per token
            
            if len(content) <= char_limit:
                return [content]
            
            # Split by paragraphs first for more natural chunks
            paragraphs = content.split('\n\n')
            chunks = []
            current_chunk = ""
            
            for para in paragraphs:
                # If adding this paragraph would exceed the limit
                if len(current_chunk) + len(para) + 2 > char_limit:  # +2 for newlines
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    # If paragraph itself is too long, split it into sentences
                    if len(para) > char_limit:
                        sentences = para.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n').split('\n')
                        current_chunk = ""
                        
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) + 1 > char_limit:  # +1 for space
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                
                                # If sentence itself is too long, split it into chunks
                                if len(sentence) > char_limit:
                                    for i in range(0, len(sentence), char_limit):
                                        chunks.append(sentence[i:i+char_limit].strip())
                                    current_chunk = ""
                                else:
                                    current_chunk = sentence
                            else:
                                if current_chunk:
                                    current_chunk += " " + sentence
                                else:
                                    current_chunk = sentence
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        else:
            # Use tiktoken for more accurate token counting
            tokens = self.tokenizer.encode(content)
            
            if len(tokens) <= safe_token_limit:
                return [content]
            
            chunks = []
            current_tokens = []
            current_chunk = ""
            
            # Split by paragraphs first for more natural chunks
            paragraphs = content.split('\n\n')
            
            for para in paragraphs:
                para_tokens = self.tokenizer.encode(para)
                
                # If adding this paragraph would exceed the limit
                if len(current_tokens) + len(para_tokens) + 2 > safe_token_limit:  # +2 for newlines
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    # If paragraph itself is too long, split it
                    if len(para_tokens) > safe_token_limit:
                        # Split into sentences for more natural chunks
                        sentences = para.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n').split('\n')
                        current_tokens = []
                        current_chunk = ""
                        
                        for sentence in sentences:
                            sentence_tokens = self.tokenizer.encode(sentence)
                            
                            if len(current_tokens) + len(sentence_tokens) + 1 > safe_token_limit:  # +1 for space
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                
                                # If sentence itself is too long, split it into chunks
                                if len(sentence_tokens) > safe_token_limit:
                                    # Split into chunks of tokens
                                    for i in range(0, len(sentence_tokens), safe_token_limit):
                                        chunk_tokens = sentence_tokens[i:i+safe_token_limit]
                                        chunk_text = self.tokenizer.decode(chunk_tokens)
                                        chunks.append(chunk_text.strip())
                                    current_tokens = []
                                    current_chunk = ""
                                else:
                                    current_tokens = sentence_tokens
                                    current_chunk = sentence
                            else:
                                if current_chunk:
                                    current_chunk += " " + sentence
                                    current_tokens.extend(sentence_tokens)
                                else:
                                    current_chunk = sentence
                                    current_tokens = sentence_tokens
                    else:
                        current_tokens = para_tokens
                        current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                        current_tokens.extend(para_tokens)
                    else:
                        current_chunk = para
                        current_tokens = para_tokens
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
    
    async def embed_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate embeddings for a document.
        
        Args:
            content: Document content
            metadata: Optional metadata about the document
            
        Returns:
            Dictionary containing document content, metadata, and embeddings
        """
        if metadata is None:
            metadata = {}
        
        # Chunk content if it's too large
        content_chunks = self.chunk_content(content, metadata=metadata)
        
        if len(content_chunks) > 1:
            print(f"Content exceeds token limit ({self.token_limit}), chunking...")
        
        # Generate embeddings for each chunk
        embeddings = []
        
        for chunk in content_chunks:
            # Skip empty chunks
            if not chunk.strip():
                continue
            
            # Generate embedding for this chunk
            embedding = await self._generate_embedding(chunk)
            
            if embedding:
                embeddings.append({
                    'content': chunk,
                    'embedding': embedding
                })
        
        return {
            'content': content,
            'metadata': metadata,
            'chunks': embeddings
        }
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a text using the Granite API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.api_url or not self.api_key or not self.model_name:
            print("Error: Missing required configuration for embedding model.")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "input": text
        }
        
        print(f"Sending request to {self.api_url} with payload length: {len(text)} characters")
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=payload)
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if "data" in response_data and len(response_data["data"]) > 0:
                        if "embedding" in response_data["data"][0]:
                            embedding = response_data["data"][0]["embedding"]
                            print(f"Successfully generated embedding with dimension: {len(embedding)}")
                            return embedding
                    
                    print(f"Error: Unexpected response format: {response_data}")
                    return None
                
                # If rate limited, wait and retry
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Rate limited, waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                
                print(f"Error: API request failed with status {response.status_code}: {response.text}")
                return None
            
            except Exception as e:
                print(f"Error generating embedding: {e}")
                
                # Wait before retrying
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        print(f"Failed to generate embedding after {self.max_retries} attempts")
        return None
    
    async def generate_embeddings(self, input_dir: str, output_dir: str) -> List[str]:
        """Generate embeddings for all documents in a directory.
        
        Args:
            input_dir: Directory containing processed documents
            output_dir: Directory to save embeddings
            
        Returns:
            List of paths to saved embedding files
        """
        ensure_directory_exists(output_dir)
        
        # Get all JSON files in the input directory
        files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
        saved_files = []
        
        # Process files in batches to manage memory usage
        for i in range(0, len(files), self.max_concurrent):
            batch = files[i:i + self.max_concurrent]
            
            log_memory_usage(prefix=f"Before embedding batch {i // self.max_concurrent + 1}: ")
            
            tasks = []
            for filename in batch:
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename.replace('.json', '_embedded.json'))
                
                # Skip if output file already exists
                if os.path.exists(output_path):
                    print(f"Skipping {filename}, embedding already exists")
                    saved_files.append(output_path)
                    continue
                
                # Load the processed document
                try:
                    data = load_json(input_path)
                    
                    # Create task for embedding generation
                    task = self.process_file(data, output_path)
                    tasks.append(task)
                
                except Exception as e:
                    print(f"Error loading {input_path}: {e}")
            
            # Run tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result, filename in zip([r for r in results if not isinstance(r, Exception)], 
                                       [f for f, t in zip(batch, tasks) if not isinstance(t, Exception)]):
                if result:
                    saved_files.append(result)
                    print(f"Generated embeddings and saved: {result}")
                else:
                    print(f"Failed to generate embeddings for {filename}")
            
            log_memory_usage(prefix=f"After embedding batch {i // self.max_concurrent + 1}: ")
        
        return saved_files
    
    async def process_file(self, data: Dict[str, Any], output_path: str) -> Optional[str]:
        """Process a single file to generate embeddings.
        
        Args:
            data: Document data
            output_path: Path to save embeddings
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            # Extract content and metadata
            content = data.get('content', '')
            metadata = data.get('metadata', {})
            
            # Generate embeddings
            result = await self.embed_document(content, metadata)
            
            # Save embeddings
            save_json(output_path, result)
            
            return output_path
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return None