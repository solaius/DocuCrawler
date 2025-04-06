"""
Advanced chunking strategies for better semantic coherence.
"""

import re
from typing import List, Dict, Any, Optional, Tuple

class AdvancedChunker:
    """Advanced chunking strategies for better semantic coherence."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the advanced chunker.
        
        Args:
            config: Dictionary containing chunker configuration
        """
        if config is None:
            config = {}
        
        self.max_chunk_size = config.get('max_chunk_size', 512)
        self.min_chunk_size = config.get('min_chunk_size', 100)
        self.overlap = config.get('overlap', 50)
        self.respect_sections = config.get('respect_sections', True)
        self.respect_paragraphs = config.get('respect_paragraphs', True)
        self.respect_sentences = config.get('respect_sentences', True)
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk text into semantically coherent chunks.
        
        Args:
            text: Text to chunk
            metadata: Metadata to include with each chunk
            
        Returns:
            List of chunks with metadata
        """
        if metadata is None:
            metadata = {}
        
        # First, try to split by sections if enabled
        if self.respect_sections and '##' in text:
            chunks = self._split_by_sections(text)
        # Otherwise, split by paragraphs if enabled
        elif self.respect_paragraphs:
            chunks = self._split_by_paragraphs(text)
        # Otherwise, split by sentences if enabled
        elif self.respect_sentences:
            chunks = self._split_by_sentences(text)
        # Otherwise, split by tokens
        else:
            chunks = self._split_by_tokens(text)
        
        # Add metadata to each chunk
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'chunk_count': len(chunks)
            })
            
            result.append({
                'content': chunk,
                'metadata': chunk_metadata
            })
        
        return result
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text by Markdown sections.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks split by sections
        """
        # Split by headings (##, ###, etc.)
        section_pattern = r'(^|\n)(#{2,}[^\n]+)'
        sections = re.split(section_pattern, text)
        
        # Combine the heading with its content
        chunks = []
        current_chunk = sections[0] if sections else ""
        
        for i in range(1, len(sections), 3):
            if i + 1 < len(sections):
                heading = sections[i] + sections[i+1]
                content = sections[i+2] if i+2 < len(sections) else ""
                
                # If adding this section would exceed max_chunk_size, start a new chunk
                if len(current_chunk) + len(heading) + len(content) > self.max_chunk_size and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = heading + content
                else:
                    current_chunk += heading + content
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # If any chunk is still too large, split it further
        result = []
        for chunk in chunks:
            if len(chunk) > self.max_chunk_size:
                if self.respect_paragraphs:
                    result.extend(self._split_by_paragraphs(chunk))
                else:
                    result.extend(self._split_by_sentences(chunk))
            else:
                result.append(chunk)
        
        return result
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks split by paragraphs
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Skip empty paragraphs
            if not paragraph.strip():
                continue
            
            # If adding this paragraph would exceed max_chunk_size, start a new chunk
            if len(current_chunk) + len(paragraph) > self.max_chunk_size and len(current_chunk) >= self.min_chunk_size:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # If any chunk is still too large, split it further
        result = []
        for chunk in chunks:
            if len(chunk) > self.max_chunk_size:
                result.extend(self._split_by_sentences(chunk))
            else:
                result.append(chunk)
        
        return result
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks split by sentences
        """
        # Simple sentence splitting (not perfect but good enough for most cases)
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Skip empty sentences
            if not sentence.strip():
                continue
            
            # If adding this sentence would exceed max_chunk_size, start a new chunk
            if len(current_chunk) + len(sentence) > self.max_chunk_size and len(current_chunk) >= self.min_chunk_size:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # If any chunk is still too large, split it by tokens
        result = []
        for chunk in chunks:
            if len(chunk) > self.max_chunk_size:
                result.extend(self._split_by_tokens(chunk))
            else:
                result.append(chunk)
        
        return result
    
    def _split_by_tokens(self, text: str) -> List[str]:
        """Split text by approximate token count.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks split by tokens
        """
        # Simple approximation: 1 token ≈ 4 characters
        chars_per_token = 4
        max_chars = self.max_chunk_size * chars_per_token
        
        # Split text into chunks of approximately max_chars
        chunks = []
        for i in range(0, len(text), max_chars - self.overlap * chars_per_token):
            chunk = text[i:i + max_chars]
            if chunk:
                chunks.append(chunk)
        
        return chunks