# DocuCrawler Documentation

Welcome to the DocuCrawler documentation! This directory contains comprehensive documentation for the DocuCrawler project.

## Overview Documents

- [Project Overview](PROJECT_OVERVIEW.md) - High-level description of the project, its goals, and architecture
- [Current State](CURRENT_STATE.md) - Current status of the project, including completed and planned features

## Installation and Setup Guides

- [Installation Guide](guides/INSTALLATION.md) - How to install and set up DocuCrawler
- [PGVector Setup](guides/PGVECTOR_SETUP.md) - How to set up PostgreSQL with pgvector extension
- [Elasticsearch Setup](guides/ELASTICSEARCH_SETUP.md) - How to set up Elasticsearch for vector search
- [Weaviate Setup](guides/WEAVIATE_SETUP.md) - How to set up Weaviate for vector search

## Usage Guides

- [Usage Guide](guides/USAGE.md) - How to use DocuCrawler for crawling, processing, and searching documentation

## API Documentation

For detailed API documentation, please refer to the docstrings in the source code. Key modules include:

- `docucrawler.crawlers` - Web crawling and content extraction
- `docucrawler.processors` - Content processing and normalization
- `docucrawler.embedders` - Embedding generation
- `docucrawler.vectordb` - Vector database integration

## Examples

Check the `examples` directory for usage examples:

- `vector_search.py` - Example of semantic search using vector databases

## Contributing

If you'd like to contribute to DocuCrawler, please see the [Contributing Guide](../CONTRIBUTING.md) for guidelines and best practices.