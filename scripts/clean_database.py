#!/usr/bin/env python3
"""
Script to clean the vector database by deleting all documents.
"""

import os
import argparse
import psycopg2
from dotenv import load_dotenv

def clean_pgvector():
    """Clean the PGVector database by deleting all documents."""
    # Load environment variables
    load_dotenv()
    
    # Get database connection details from environment variables
    pgvector_url = os.getenv('PGVECTOR_URL', 'localhost:5432')
    
    # Handle different URL formats (with or without protocol)
    if '//' in pgvector_url:
        # URL with protocol (e.g., http://hostname:port)
        from urllib.parse import urlparse
        parsed_url = urlparse(pgvector_url)
        host = parsed_url.hostname or 'localhost'
        port = parsed_url.port or 5432
    elif ':' in pgvector_url:
        # Simple host:port format
        parts = pgvector_url.split(':')
        host = parts[0]
        port = int(parts[1])
    else:
        # Just hostname
        host = pgvector_url
        port = 5432
    database = os.getenv('PGVECTOR_DB', 'postgres')
    user = os.getenv('PGVECTOR_USER', 'postgres')
    password = os.getenv('PGVECTOR_PASSWORD', 'postgres')
    
    try:
        # Connect to the database
        print(f"Connecting to PostgreSQL database at {host}:{port}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check if the documents table exists
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'documents')")
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            # Count documents before deletion
            cur.execute("SELECT COUNT(*) FROM documents")
            count_before = cur.fetchone()[0]
            print(f"Documents before deletion: {count_before}")
            
            # Delete all documents
            cur.execute("DELETE FROM documents")
            conn.commit()
            
            # Count documents after deletion
            cur.execute("SELECT COUNT(*) FROM documents")
            count_after = cur.fetchone()[0]
            print(f"Documents after deletion: {count_after}")
            
            print(f"Successfully deleted {count_before - count_after} documents from the database.")
        else:
            print("The 'documents' table does not exist in the database.")
        
        # Close the cursor and connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error cleaning PGVector database: {e}")

def clean_elasticsearch():
    """Clean the Elasticsearch database by deleting all indices."""
    # This would be implemented if Elasticsearch is used
    print("Elasticsearch cleaning not implemented yet.")

def clean_weaviate():
    """Clean the Weaviate database by deleting all classes."""
    # This would be implemented if Weaviate is used
    print("Weaviate cleaning not implemented yet.")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Clean vector database by deleting all documents')
    parser.add_argument('--db-type', choices=['pgvector', 'elasticsearch', 'weaviate'], default='pgvector',
                        help='Type of vector database to clean')
    
    args = parser.parse_args()
    
    if args.db_type == 'pgvector':
        clean_pgvector()
    elif args.db_type == 'elasticsearch':
        clean_elasticsearch()
    elif args.db_type == 'weaviate':
        clean_weaviate()

if __name__ == "__main__":
    main()