# DocuCrawler Installation Guide

This guide provides step-by-step instructions for installing DocuCrawler and its dependencies.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

## Basic Installation

1. **Clone the repository**

```bash
git clone https://github.com/solaius/DocuCrawler.git
cd DocuCrawler
```

2. **Create a virtual environment (recommended)**

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root directory with the following content:

```
# Embedding API Configuration
GRANITE_EMBEDDINGS_URL=your_embeddings_api_url
GRANITE_EMBEDDINGS_API=your_api_key
GRANITE_EMBEDDINGS_MODEL_NAME=your_model_name
EMBEDDINGS_TOKEN_LIMIT=512

# Vector Database Configuration (choose one)
# PGVector
PGVECTOR_URL=localhost:5432
PGVECTOR_DB=postgres
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=postgres

# Elasticsearch (optional)
# ELASTICSEARCH_URL=http://localhost:9200
# ELASTICSEARCH_INDEX=docucrawler
# ELASTICSEARCH_USER=elastic
# ELASTICSEARCH_PASSWORD=changeme

# Weaviate (optional)
# WEAVIATE_URL=http://localhost:8080
# WEAVIATE_API_KEY=
# WEAVIATE_CLASS=DocuCrawler
```

5. **Install the package in development mode**

```bash
pip install -e .
```

## Running DocuCrawler

```bash
# Run the complete pipeline
python main.py

# Run specific steps
python main.py --steps crawl preprocess

# Process specific sources
python main.py --sources langchain mcp

# Use a specific vector database
python main.py --db-type pgvector
```

## Docker Installation

1. **Build the Docker image**

```bash
docker build -t docucrawler .
```

2. **Run the container**

```bash
docker run -v ./data:/app/data -v ./.env:/app/.env docucrawler
```

3. **Using Docker Compose**

```bash
docker-compose up
```

## Troubleshooting

- **Missing dependencies**: If you encounter errors about missing packages, try running `pip install -r requirements.txt` again.
- **Environment variables**: Ensure your `.env` file is properly configured with valid API keys and URLs.
- **Permission issues**: Make sure you have write permissions to the directories where DocuCrawler will store data.
- **Memory errors**: For large documentation sets, you may need to increase available memory or process fewer sources at once.