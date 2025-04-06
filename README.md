# DocuCrawler

DocuCrawler is an intelligent, extensible documentation aggregation system that pulls the latest documentation, examples, and guides from various software products to support rapid software development.

## Features

- Automated collection and processing of documentation across multiple sources
- Structured output in markdown/JSON format for easy consumption by downstream systems
- Integration with embedding models for semantic search capabilities
- Vector database integration for efficient semantic search (PGVector, Elasticsearch, Weaviate)
- Modular architecture for easy extension to new documentation sources

## Supported Documentation Sources

- LangChain
- Docling
- Meta Llama Stack
- Model Context Protocol (MCP)

## Documentation

For comprehensive documentation, please see the [documentation directory](documentation/README.md):

- [Project Overview](documentation/PROJECT_OVERVIEW.md) - Vision, objectives, and architecture
- [Current State](documentation/CURRENT_STATE.md) - Completed features and roadmap
- [Installation Guide](documentation/guides/INSTALLATION.md) - How to install DocuCrawler
- [Usage Guide](documentation/guides/USAGE.md) - How to use DocuCrawler

### Vector Database Setup Guides

- [PGVector Setup](documentation/guides/PGVECTOR_SETUP.md)
- [Elasticsearch Setup](documentation/guides/ELASTICSEARCH_SETUP.md)
- [Weaviate Setup](documentation/guides/WEAVIATE_SETUP.md)

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Vector database (PGVector, Elasticsearch, or Weaviate)

### Install from source

```bash
# Clone the repository
git clone https://github.com/solaius/DocuCrawler.git
cd DocuCrawler

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root with the following variables:

```
# Embedding API Configuration
GRANITE_EMBEDDINGS_URL=https://your-embeddings-api-url/v1/embeddings
GRANITE_EMBEDDINGS_API=your-api-key
GRANITE_EMBEDDINGS_MODEL_NAME=your-model-name
EMBEDDINGS_TOKEN_LIMIT=512

# Vector Database Configuration (choose one)
# PGVector
PGVECTOR_URL=localhost:5432
PGVECTOR_DB=postgres
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=postgres
```

## Usage

### Command Line Interface

```bash
# Run the complete pipeline
python main.py

# Run specific steps
python main.py --steps crawl preprocess

# Process specific sources
python main.py --sources langchain mcp

# Use a specific vector database
python main.py --db-type pgvector

# Combine options
python main.py --steps crawl preprocess embed --sources mcp --db-type elasticsearch
```

### Semantic Search

```bash
# Search for documents related to your query
python examples/vector_search.py "your search query" --collection mcp --db-type pgvector
```

For more detailed usage instructions, see the [Usage Guide](documentation/guides/USAGE.md).

## Project Structure

```
DocuCrawler/
├── docucrawler/                  # Main package
│   ├── crawlers/                 # Web crawling modules
│   │   ├── base.py               # Base crawler interface
│   │   ├── web_crawler.py        # Web crawler implementation
│   │   └── connectors.py         # Source-specific connectors
│   ├── processors/               # Document processing modules
│   │   ├── base.py               # Base processor interface
│   │   └── markdown_processor.py # Markdown processor implementation
│   ├── embedders/                # Embedding generation modules
│   │   ├── base.py               # Base embedder interface
│   │   └── granite_embedder.py   # Granite embedder implementation
│   ├── vectordb/                 # Vector database modules
│   │   ├── base.py               # Base vector database interface
│   │   ├── pgvector_db.py        # PGVector implementation
│   │   ├── elasticsearch_db.py   # Elasticsearch implementation
│   │   ├── weaviate_db.py        # Weaviate implementation
│   │   ├── factory.py            # Vector database factory
│   │   └── integration.py        # Integration with embedding pipeline
│   └── utils/                    # Utility functions
│       └── common.py             # Common utility functions
├── data/                         # Data storage directory
│   ├── crawled/                  # Raw crawled content
│   ├── processed/                # Processed content
│   └── embeddings/               # Generated embeddings
├── documentation/                # Project documentation
├── examples/                     # Example scripts
├── main.py                       # Main entry point
├── setup.py                      # Package setup script
├── requirements.txt              # Dependencies
└── .env                          # Environment variables (not in version control)
```

## Contributing

Contributions to DocuCrawler are welcome! Here are some ways you can contribute:

- Report bugs and suggest features by opening issues
- Submit pull requests to fix issues or add new features
- Improve documentation
- Add support for new documentation sources
- Implement connectors for additional vector databases

Please see the [Contributing Guide](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.