# DocuCrawler Usage Guide

This guide provides detailed instructions on how to use DocuCrawler for crawling, processing, and searching documentation.

## Basic Usage

DocuCrawler provides a command-line interface for running the documentation pipeline. The basic command structure is:

```bash
python main.py [--steps STEPS [STEPS ...]] [--sources SOURCES [SOURCES ...]] [--db-type DB_TYPE]
```

### Parameters

- `--steps`: Specify which steps to run (default: all steps)
  - Available steps: `crawl`, `preprocess`, `embed`, `vectordb`
  - Example: `--steps crawl preprocess`

- `--sources`: Specify which documentation sources to process (default: all sources)
  - Available sources: `langchain`, `docling`, `llama-stack`, `mcp`
  - Example: `--sources langchain mcp`

- `--db-type`: Specify which vector database to use (default: determined from environment)
  - Available databases: `pgvector`, `elasticsearch`, `weaviate`
  - Example: `--db-type pgvector`

### Examples

1. **Run the complete pipeline for all sources**

```bash
python main.py
```

2. **Only crawl and preprocess LangChain documentation**

```bash
python main.py --steps crawl preprocess --sources langchain
```

3. **Generate embeddings and store them in Elasticsearch**

```bash
python main.py --steps embed vectordb --db-type elasticsearch
```

4. **Process MCP documentation and store in PGVector**

```bash
python main.py --sources mcp --db-type pgvector
```

## Pipeline Steps

### 1. Crawling

The crawling step fetches documentation from the specified sources and saves the raw content to the `data/crawled` directory.

```bash
python main.py --steps crawl
```

This step:
- Retrieves URLs from sitemaps or predefined lists
- Fetches content using Playwright for JavaScript-rendered pages
- Saves the raw content as markdown files

### 2. Preprocessing

The preprocessing step cleans and normalizes the crawled content and saves it to the `data/processed` directory.

```bash
python main.py --steps preprocess
```

This step:
- Cleans and normalizes markdown content
- Extracts metadata (title, headings, etc.)
- Formats content for embedding generation
- Saves processed content as JSON files

### 3. Embedding Generation

The embedding step generates vector embeddings for the processed content and saves them to the `data/embeddings` directory.

```bash
python main.py --steps embed
```

This step:
- Chunks content into appropriate sizes for the embedding model
- Generates embeddings using the configured API
- Handles large documents through intelligent chunking
- Saves embeddings as JSON files

### 4. Vector Database Integration

The vector database step stores the generated embeddings in the specified vector database for efficient retrieval.

```bash
python main.py --steps vectordb --db-type pgvector
```

This step:
- Connects to the specified vector database
- Creates collections/indices as needed
- Stores document content and embeddings
- Enables semantic search capabilities

## Semantic Search

DocuCrawler provides a simple example script for performing semantic searches on the stored documentation:

```bash
python examples/vector_search.py "your search query" --collection mcp --db-type pgvector
```

### Parameters

- First argument: The search query
- `--collection`: The collection to search in (default: mcp)
- `--db-type`: The vector database to use (default: pgvector)
- `--limit`: Maximum number of results to return (default: 5)

### Examples

1. **Search for information about LLMs in MCP documentation**

```bash
python examples/vector_search.py "How to use LLMs with MCP" --collection mcp
```

2. **Search in LangChain documentation using Elasticsearch**

```bash
python examples/vector_search.py "RAG implementation" --collection langchain --db-type elasticsearch
```

3. **Get more results from Weaviate**

```bash
python examples/vector_search.py "vector database integration" --collection docling --db-type weaviate --limit 10
```

## Advanced Usage

### Custom Configuration

You can customize DocuCrawler by modifying the `.env` file or by creating source-specific configuration files.

### Adding New Sources

To add a new documentation source:

1. Create a new connector class in `docucrawler/crawlers/connectors.py`
2. Implement the required methods (see existing connectors for examples)
3. Add the source to the available sources in `main.py`

### Using Different Embedding Models

To use a different embedding model:

1. Update the `.env` file with the new model's API details
2. Modify the embedding generation code if necessary

### Programmatic Usage

You can use DocuCrawler programmatically in your own Python code:

```python
import asyncio
from docucrawler.crawlers import LangChainConnector
from docucrawler.processors import MarkdownProcessor
from docucrawler.embedders import GraniteEmbedder
from docucrawler.vectordb.integration import store_embeddings, search_documents

# Example: Crawl and process a specific URL
async def process_url(url):
    connector = LangChainConnector()
    result = await connector.crawl_url(url)
    
    processor = MarkdownProcessor()
    processed = processor.process_content(result.markdown.raw_markdown)
    
    embedder = GraniteEmbedder()
    embedding = await embedder.embed_document(processed['content'])
    
    return embedding

# Example: Search for similar documents
async def search(query):
    results = await search_documents(
        query_embedding=query_embedding,
        db_type='pgvector',
        collection_name='langchain'
    )
    return results

# Run the async functions
asyncio.run(process_url("https://example.com/docs"))
```

## Troubleshooting

- **Crawling issues**: Check network connectivity and website robots.txt rules
- **Processing errors**: Inspect the raw content for unusual formatting
- **Embedding failures**: Verify API keys and rate limits
- **Database connection problems**: Ensure the database is running and accessible
- **Memory errors**: For large documentation sets, try processing fewer sources at once