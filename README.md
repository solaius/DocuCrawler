# DocuCrawler

DocuCrawler is an intelligent, extensible documentation aggregation system that pulls the latest documentation, examples, and guides from various software products to support rapid software development.

## Features

- Automated collection and processing of documentation across multiple sources
- Structured output in markdown/JSON format for easy consumption by downstream systems
- Integration with embedding models for semantic search capabilities
- Modular architecture for easy extension to new documentation sources

## Supported Documentation Sources

- LangChain
- Docling
- Meta Llama Stack
- MCP (Red Hat Build of Microshift)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from source

```bash
# Clone the repository
git clone https://github.com/solaius/DocuCrawler.git
cd DocuCrawler

# Install the package
pip install -e .

# For language detection support
pip install -e ".[language_detection]"
```

## Configuration

DocuCrawler uses environment variables for configuration. Create a `.env` file in the project root with the following variables:

```
# Granite Embeddings API Configuration
GRANITE_EMBEDDINGS_URL=https://your-embeddings-api-url/v1/embeddings
GRANITE_EMBEDDINGS_API=your-api-key
GRANITE_EMBEDDINGS_MODEL_NAME=your-model-name

# Token limit for embedding model
EMBEDDINGS_TOKEN_LIMIT=512
```

## Usage

### Command Line Interface

```bash
# Run the complete pipeline
python main.py

# Run specific steps
python main.py --steps crawl preprocess

# Process specific sources
python main.py --sources langchain llama-stack

# Combine step and source filtering
python main.py --steps crawl preprocess --sources mcp
```

### Python API

```python
import asyncio
from docucrawler.crawlers.connectors import LangChainConnector
from docucrawler.processors.markdown_processor import MarkdownProcessor
from docucrawler.embedders.granite_embedder import GraniteEmbedder

# Crawl documentation
async def crawl_langchain():
    connector = LangChainConnector()
    files = await connector.crawl_documentation()
    print(f"Crawled {len(files)} files")

# Process documents
async def process_documents():
    processor = MarkdownProcessor({'max_concurrent': 10})
    files = await processor.process('docs/crawled/langchain', 'docs/processed/langchain')
    print(f"Processed {len(files)} files")

# Generate embeddings
async def generate_embeddings():
    embedder = GraniteEmbedder({
        'api_url': 'your-api-url',
        'api_key': 'your-api-key',
        'model_name': 'your-model-name',
        'token_limit': 512
    })
    files = await embedder.generate_embeddings('docs/processed/langchain', 'docs/embeddings/langchain')
    print(f"Generated embeddings for {len(files)} files")

# Run the functions
asyncio.run(crawl_langchain())
asyncio.run(process_documents())
asyncio.run(generate_embeddings())
```

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
│   └── utils/                    # Utility functions
│       └── common.py             # Common utility functions
├── main.py                       # Main entry point
├── setup.py                      # Package setup script
├── requirements.txt              # Dependencies
└── .env                          # Environment variables (not in version control)
```

## Extending DocuCrawler

### Adding a New Documentation Source

1. Create a new connector class in `docucrawler/crawlers/connectors.py` that inherits from `WebCrawler`
2. Configure the sitemap URL, base URL, and other parameters
3. Implement the `crawl_documentation` method
4. Add the new source to the `sources` list in `main.py`

### Adding a New Processor

1. Create a new processor class in `docucrawler/processors/` that inherits from `BaseProcessor`
2. Implement the `process_document` and `process` methods
3. Update `main.py` to use the new processor

### Adding a New Embedder

1. Create a new embedder class in `docucrawler/embedders/` that inherits from `BaseEmbedder`
2. Implement the `embed_document`, `chunk_content`, and `generate_embeddings` methods
3. Update `main.py` to use the new embedder

## License

This project is licensed under the MIT License - see the LICENSE file for details.