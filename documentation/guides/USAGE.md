# DocuCrawler Usage Guide

This guide provides detailed instructions on how to use DocuCrawler for crawling, processing, and searching documentation.

## Basic Usage

DocuCrawler provides a command-line interface for running the documentation pipeline. The basic command structure is:

```bash
python main.py [--steps STEPS [STEPS ...]] [--sources SOURCES [SOURCES ...]] [--db-type DB_TYPE] [--full] [--basic-chunking]
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

- `--incremental`: Enable incremental crawling to only process changed documents (default: enabled)
  - This saves time and resources by skipping unchanged documents

- `--full`: Force full crawling, processing all documents even if unchanged
  - Use this when you want to rebuild the entire database

- `--advanced-chunking`: Enable advanced chunking for better semantic coherence (default: enabled)
  - This creates chunks that respect document structure (sections, paragraphs)

- `--basic-chunking`: Use basic chunking instead of advanced chunking
  - Use this for simpler, token-based chunking

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

5. **Force full crawling (disable incremental updates)**

```bash
python main.py --full
```

6. **Use basic chunking instead of advanced chunking**

```bash
python main.py --basic-chunking
```

7. **Combine multiple options**

```bash
python main.py --sources mcp --db-type pgvector --full --basic-chunking
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
- Tracks document changes for incremental updates
- Skips unchanged documents when in incremental mode
- Saves the raw content as markdown files

By default, DocuCrawler uses incremental crawling, which only processes documents that have changed since the last run. This saves time and resources, especially for large documentation sets. You can force a full crawl with the `--full` flag.

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
- Uses advanced chunking strategies that respect document structure (sections, paragraphs)
- Generates embeddings using the configured API
- Handles large documents through intelligent chunking
- Saves embeddings as JSON files

DocuCrawler uses advanced chunking by default, which creates chunks that respect document structure for better semantic coherence. This results in more meaningful search results. You can switch to basic chunking with the `--basic-chunking` flag if needed.

### 4. Vector Database Integration

The vector database step stores the generated embeddings in the specified vector database for efficient retrieval.

```bash
python main.py --steps vectordb --db-type pgvector
```

This step:
- Connects to the specified vector database
- Creates collections/indices as needed
- Stores document content and embeddings
- Handles chunked documents intelligently
- Enables semantic search capabilities

When using advanced chunking, the system stores each chunk as a separate document in the vector database, but maintains the relationship between chunks and their parent documents. This allows for more precise search results while still providing context.

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
- `--no-group`: Do not group chunks from the same document (show individual chunks)

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

4. **Show individual chunks instead of grouped results**

```bash
python examples/vector_search.py "MCP architecture" --collection mcp --no-group
```

When using advanced chunking, search results are grouped by default, showing the most relevant chunks from each document. If you want to see individual chunks as separate results, use the `--no-group` flag.

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