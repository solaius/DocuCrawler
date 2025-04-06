# DocuCrawler - Project Overview

## Vision

DocuCrawler is an intelligent, extensible documentation aggregation system designed to pull the latest documentation, examples, and guides from various software products to support rapid software development. It automates the collection, processing, and indexing of technical documentation, making it easily searchable and accessible.

## Core Objectives

1. **Automated Documentation Collection**
   - Crawl and extract documentation from multiple sources
   - Support various documentation formats and structures
   - Handle dynamic content and JavaScript-rendered pages

2. **Intelligent Processing**
   - Clean and normalize documentation content
   - Extract meaningful structure and metadata
   - Support multilingual content

3. **Semantic Search Capabilities**
   - Generate high-quality embeddings for documentation content
   - Store embeddings in vector databases for efficient retrieval
   - Provide natural language search capabilities

4. **Extensibility and Flexibility**
   - Support multiple documentation sources through a plugin architecture
   - Allow for easy integration of new vector databases
   - Provide a modular design for customization

## Architecture

DocuCrawler follows a modular architecture with the following components:

1. **Crawlers**
   - Web crawlers for extracting content from documentation sites
   - Source-specific connectors for specialized documentation formats
   - URL filtering and rate limiting to respect website policies

2. **Processors**
   - Content cleaning and normalization
   - Metadata extraction
   - Language detection and multilingual support

3. **Embedders**
   - Text chunking and tokenization
   - Embedding generation using AI models
   - Handling of large documents through intelligent chunking

4. **Vector Databases**
   - Storage of document embeddings for efficient retrieval
   - Support for multiple vector database backends (PGVector, Elasticsearch, Weaviate)
   - Semantic search capabilities

5. **Utilities**
   - Common functions for file handling, logging, and configuration
   - Memory usage monitoring
   - Error handling and retry logic

## Current Supported Sources

- LangChain Documentation
- Docling Documentation
- Meta Llama Stack Documentation
- Model Context Protocol (MCP) Documentation

## Roadmap

### Phase 1: Core Functionality (Completed)
- ✅ Basic crawling and content extraction
- ✅ Content preprocessing and cleaning
- ✅ Embedding generation
- ✅ Vector database integration

### Phase 2: Enhanced Capabilities (In Progress)
- 🔄 Improved error handling and logging
- 🔄 Advanced content extraction for complex documentation
- 🔄 Better chunking strategies for large documents
- 🔄 Incremental updates to avoid redundant processing

### Phase 3: User Interface and API (Planned)
- 📅 Web dashboard for monitoring and management
- 📅 REST API for programmatic access
- 📅 Command-line interface improvements
- 📅 Search interface for end users

### Phase 4: Advanced Features (Planned)
- 📅 Automated documentation summarization
- 📅 Topic modeling and categorization
- 📅 Cross-reference detection between documents
- 📅 Question answering capabilities

### Phase 5: Enterprise Features (Future)
- 📅 Authentication and access control
- 📅 Multi-user support
- 📅 Integration with knowledge management systems
- 📅 Custom plugins for enterprise documentation sources

## Technology Stack

- **Programming Language**: Python 3.8+
- **Web Crawling**: crawl4ai, Playwright
- **Text Processing**: tiktoken, langdetect
- **Embedding Models**: Granite Embedding API
- **Vector Databases**: PGVector, Elasticsearch, Weaviate
- **Database ORM**: SQLAlchemy
- **Asynchronous Programming**: asyncio, aiohttp, asyncpg

## Contributing

DocuCrawler is designed to be community-driven. Contributions are welcome in the following areas:

1. **New Source Connectors**: Add support for additional documentation sources
2. **Vector Database Integrations**: Implement connectors for other vector databases
3. **Preprocessing Improvements**: Enhance content cleaning and normalization
4. **Performance Optimizations**: Improve efficiency and resource usage
5. **Documentation**: Improve guides, tutorials, and API documentation

## License

DocuCrawler is released under the MIT License. See the LICENSE file for details.