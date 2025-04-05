"""
Markdown document processor implementation.
"""

import os
import re
import asyncio
from typing import Dict, Any, List

from docucrawler.processors.base import BaseProcessor
from docucrawler.utils.common import (
    ensure_directory_exists, log_memory_usage, load_text, save_json
)


class MarkdownProcessor(BaseProcessor):
    """Processor for Markdown documents."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the markdown processor.
        
        Args:
            config: Dictionary containing processor configuration
        """
        super().__init__(config)
        self.max_concurrent = config.get('max_concurrent', 10)
        self.summary_length = config.get('summary_length', 200)
        self.language_detection = config.get('language_detection', False)
    
    def process_document(self, content: str) -> Dict[str, Any]:
        """Process a single markdown document.
        
        Args:
            content: Document content to process
            
        Returns:
            Processed document as a dictionary
        """
        cleaned_content = self._clean_markdown(content)
        
        # Extract title from the first line or heading
        title_match = re.search(r'^#\s+(.+)$', cleaned_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)
        else:
            # Use the first line as title if no heading found
            title = cleaned_content.split('\n', 1)[0]
        
        # Detect language if enabled
        language = None
        if self.language_detection:
            try:
                from langdetect import detect
                language = detect(cleaned_content)
            except ImportError:
                print("Warning: langdetect not installed. Language detection disabled.")
            except Exception as e:
                print(f"Error detecting language: {e}")
        
        return {
            "title": title,
            "summary": cleaned_content[:self.summary_length],
            "content": cleaned_content,
            "metadata": {
                "length": len(cleaned_content),
                "language": language
            }
        }
    
    def _clean_markdown(self, content: str) -> str:
        """Clean and preprocess markdown content.
        
        Args:
            content: Markdown content to clean
            
        Returns:
            Cleaned markdown content
        """
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove Markdown links but keep the text
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        # Remove images
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        
        # Remove code blocks
        content = re.sub(r'```[\s\S]*?```', '', content)
        
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        
        # Remove repetitive patterns like "\n * \n" or "* - *"
        content = re.sub(r'(\n\s*[*-]+\s*)+', '\n', content)
        
        # Remove multiple punctuation marks
        content = re.sub(r'[.]{3,}', '.', content)
        
        # Replace sequences of asterisks or dashes
        content = re.sub(r'[*-]{2,}', '', content)
        
        # Remove excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Trim whitespace
        return content.strip()
    
    async def process(self, input_dir: str, output_dir: str) -> List[str]:
        """Process documents in the input directory and save results to output directory.
        
        Args:
            input_dir: Directory containing documents to process
            output_dir: Directory to save processed documents
            
        Returns:
            List of paths to processed files
        """
        ensure_directory_exists(output_dir)
        processed_files = []
        
        # Get all markdown files in the input directory
        files = [f for f in os.listdir(input_dir) if f.endswith(('.md', '.txt'))]
        
        for i in range(0, len(files), self.max_concurrent):
            batch = files[i:i + self.max_concurrent]
            log_memory_usage(prefix=f"Before batch {i // self.max_concurrent + 1}: ")
            
            # Create a new list of tasks for the current batch
            tasks = [
                asyncio.to_thread(
                    self._process_and_save_document,
                    os.path.join(input_dir, filename),
                    os.path.join(output_dir, filename.replace('.md', '.json').replace('.txt', '.json'))
                )
                for filename in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            processed_files.extend([path for path in batch_results if path])
            
            log_memory_usage(prefix=f"After batch {i // self.max_concurrent + 1}: ")
        
        return processed_files
    
    def _process_and_save_document(self, input_filepath: str, output_filepath: str) -> str:
        """Process a document and save the output.
        
        Args:
            input_filepath: Path to the input document
            output_filepath: Path to save the processed document
            
        Returns:
            Path to the processed document or empty string if processing failed
        """
        try:
            content = load_text(input_filepath)
            processed_data = self.process_document(content)
            
            # Add source file information
            processed_data["metadata"]["source_file"] = input_filepath
            
            save_json(output_filepath, processed_data)
            print(f"Processed and saved: {input_filepath} -> {output_filepath}")
            return output_filepath
        except Exception as e:
            print(f"Error processing {input_filepath}: {e}")
            return ""