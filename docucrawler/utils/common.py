"""
Common utility functions used across the application.
"""

import os
import json
import psutil
from typing import Dict, Any, Optional


def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists.
    
    Args:
        directory: Directory path to create if it doesn't exist
    """
    os.makedirs(directory, exist_ok=True)


def log_memory_usage(prefix: str = "") -> int:
    """Log current memory usage.
    
    Args:
        prefix: Prefix for the log message
        
    Returns:
        Current memory usage in MB
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    current_memory = memory_info.rss // (1024 * 1024)  # Convert to MB
    print(f"{prefix} Current Memory Usage: {current_memory} MB")
    return current_memory


def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON data from a file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded JSON data as a dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_json(filepath: str, data: Dict[str, Any], indent: Optional[int] = 4) -> None:
    """Save data to a JSON file.
    
    Args:
        filepath: Path to save the JSON file
        data: Data to save
        indent: Indentation level for the JSON file (None for compact JSON)
    """
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=indent)


def load_text(filepath: str) -> str:
    """Load text data from a file.
    
    Args:
        filepath: Path to the text file
        
    Returns:
        Loaded text data as a string
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()


def save_text(filepath: str, data: str) -> None:
    """Save text data to a file.
    
    Args:
        filepath: Path to save the text file
        data: Text data to save
    """
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(data)