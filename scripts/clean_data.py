#!/usr/bin/env python3
"""
Script to clean the data directories by removing all files.
"""

import os
import argparse
import shutil

def clean_data_directories(sources=None, steps=None):
    """Clean the data directories for specified sources and steps.
    
    Args:
        sources: List of sources to clean (default: all sources)
        steps: List of steps to clean (default: all steps)
    """
    if sources is None:
        sources = ['langchain', 'docling', 'llama-stack', 'mcp']
    
    if steps is None:
        steps = ['crawled', 'processed', 'embeddings']
    
    base_dir = 'data'
    
    for step in steps:
        for source in sources:
            directory = os.path.join(base_dir, step, source)
            if os.path.exists(directory):
                print(f"Cleaning {directory}...")
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                print(f"Successfully cleaned {directory}")
            else:
                print(f"Directory {directory} does not exist, skipping")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Clean data directories by removing all files')
    parser.add_argument('--sources', nargs='+', choices=['langchain', 'docling', 'llama-stack', 'mcp'],
                        help='Specify which documentation sources to clean (default: all sources)')
    parser.add_argument('--steps', nargs='+', choices=['crawled', 'processed', 'embeddings'],
                        help='Specify which steps to clean (default: all steps)')
    
    args = parser.parse_args()
    
    clean_data_directories(args.sources, args.steps)

if __name__ == "__main__":
    main()