"""
Document tracker for tracking document changes and versions.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class DocumentTracker:
    """Track document changes and versions."""
    
    def __init__(self, metadata_dir: str = 'data/metadata'):
        """Initialize the document tracker.
        
        Args:
            metadata_dir: Directory to store document metadata
        """
        self.metadata_dir = metadata_dir
        os.makedirs(metadata_dir, exist_ok=True)
    
    def _get_metadata_path(self, source: str) -> str:
        """Get the path to the metadata file for a source.
        
        Args:
            source: Source name
            
        Returns:
            Path to the metadata file
        """
        return os.path.join(self.metadata_dir, f"{source}_metadata.json")
    
    def _load_metadata(self, source: str) -> Dict[str, Any]:
        """Load metadata for a source.
        
        Args:
            source: Source name
            
        Returns:
            Metadata dictionary
        """
        metadata_path = self._get_metadata_path(source)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Invalid metadata file for {source}, creating new one")
                return {'documents': {}, 'last_crawl': None}
        return {'documents': {}, 'last_crawl': None}
    
    def _save_metadata(self, source: str, metadata: Dict[str, Any]) -> None:
        """Save metadata for a source.
        
        Args:
            source: Source name
            metadata: Metadata dictionary
        """
        metadata_path = self._get_metadata_path(source)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute a hash of the content.
        
        Args:
            content: Document content
            
        Returns:
            Content hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def update_document(self, source: str, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, bool]:
        """Update document metadata and check if it has changed.
        
        Args:
            source: Source name
            document_id: Document ID
            content: Document content
            metadata: Additional metadata
            
        Returns:
            Tuple of (is_new, has_changed)
        """
        if metadata is None:
            metadata = {}
        
        # Load existing metadata
        source_metadata = self._load_metadata(source)
        documents = source_metadata['documents']
        
        # Compute content hash
        content_hash = self._compute_content_hash(content)
        
        # Check if document exists and has changed
        is_new = document_id not in documents
        has_changed = True
        
        if not is_new:
            # Document exists, check if it has changed
            previous_hash = documents[document_id].get('content_hash')
            has_changed = previous_hash != content_hash
        
        # Update document metadata
        current_time = datetime.now().isoformat()
        
        if is_new:
            # New document
            documents[document_id] = {
                'content_hash': content_hash,
                'created_at': current_time,
                'updated_at': current_time,
                'version': 1,
                'metadata': metadata
            }
        elif has_changed:
            # Document has changed
            documents[document_id]['content_hash'] = content_hash
            documents[document_id]['updated_at'] = current_time
            documents[document_id]['version'] += 1
            documents[document_id]['metadata'].update(metadata)
        
        # Update last crawl time
        source_metadata['last_crawl'] = current_time
        
        # Save metadata
        self._save_metadata(source, source_metadata)
        
        return is_new, has_changed
    
    def get_document_metadata(self, source: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a document.
        
        Args:
            source: Source name
            document_id: Document ID
            
        Returns:
            Document metadata or None if not found
        """
        source_metadata = self._load_metadata(source)
        documents = source_metadata['documents']
        
        return documents.get(document_id)
    
    def get_all_document_ids(self, source: str) -> List[str]:
        """Get all document IDs for a source.
        
        Args:
            source: Source name
            
        Returns:
            List of document IDs
        """
        source_metadata = self._load_metadata(source)
        return list(source_metadata['documents'].keys())
    
    def get_last_crawl_time(self, source: str) -> Optional[str]:
        """Get the last crawl time for a source.
        
        Args:
            source: Source name
            
        Returns:
            Last crawl time as ISO format string or None if never crawled
        """
        source_metadata = self._load_metadata(source)
        return source_metadata.get('last_crawl')
    
    def mark_document_deleted(self, source: str, document_id: str) -> bool:
        """Mark a document as deleted.
        
        Args:
            source: Source name
            document_id: Document ID
            
        Returns:
            True if document was found and marked as deleted, False otherwise
        """
        source_metadata = self._load_metadata(source)
        documents = source_metadata['documents']
        
        if document_id in documents:
            documents[document_id]['deleted'] = True
            documents[document_id]['deleted_at'] = datetime.now().isoformat()
            self._save_metadata(source, source_metadata)
            return True
        
        return False