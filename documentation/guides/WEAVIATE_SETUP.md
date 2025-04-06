# Weaviate Setup Guide

This guide provides step-by-step instructions for setting up Weaviate for use with DocuCrawler.

## Prerequisites

- Docker (recommended for easy setup)
- Docker Compose
- 4GB+ of RAM available for Weaviate

## Option 1: Using Docker (Recommended)

1. **Create a Docker Compose file for Weaviate**

Create a file named `docker-compose-weaviate.yml` with the following content:

```yaml
version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    container_name: docucrawler-weaviate
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate-data:/var/lib/weaviate
    restart: on-failure:0

volumes:
  weaviate-data:
```

2. **Start the Weaviate container**

```bash
docker-compose -f docker-compose-weaviate.yml up -d
```

3. **Wait for Weaviate to start**

It may take a minute or two for Weaviate to fully start. You can check the logs with:

```bash
docker logs -f docucrawler-weaviate
```

4. **Verify the installation**

```bash
curl http://localhost:8080/v1/meta
```

You should see a JSON response with Weaviate version information.

5. **Update your DocuCrawler .env file**

```
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_CLASS=DocuCrawler
```

## Option 2: Using Weaviate Cloud Service (WCS)

1. **Sign up for Weaviate Cloud Service**

Go to [Weaviate Cloud Console](https://console.weaviate.cloud/) and sign up for an account.

2. **Create a new cluster**

- Click "Create Cluster"
- Choose a name for your cluster
- Select a plan (Sandbox is free)
- Choose a region close to you
- Click "Create"

3. **Get your cluster details**

Once your cluster is ready, you'll see:
- Cluster URL
- API Key

4. **Update your DocuCrawler .env file**

```
WEAVIATE_URL=https://your-cluster-url.weaviate.cloud
WEAVIATE_API_KEY=your-api-key
WEAVIATE_CLASS=DocuCrawler
```

## Verifying the Setup

To verify that Weaviate is properly set up and working with DocuCrawler:

1. **Run the vector database test**

```bash
python examples/vector_search.py "test query" --db-type weaviate
```

If everything is set up correctly, you should see a successful connection message and search results (if you have already indexed some documents).

## Advanced Configuration

### Enabling Authentication

If you want to enable authentication for your local Weaviate instance:

1. **Generate an API key**

You can use any secure random string as your API key.

2. **Update the Docker Compose file**

```yaml
environment:
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
  AUTHENTICATION_APIKEY_ENABLED: 'true'
  AUTHENTICATION_APIKEY_ALLOWED_KEYS: 'your-api-key'
```

3. **Update your DocuCrawler .env file**

```
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-api-key
WEAVIATE_CLASS=DocuCrawler
```

### Using a Text2Vec Module

If you want to use Weaviate's built-in vectorization capabilities:

1. **Update the Docker Compose file**

```yaml
environment:
  DEFAULT_VECTORIZER_MODULE: 'text2vec-transformers'
  ENABLE_MODULES: 'text2vec-transformers'
  TRANSFORMERS_INFERENCE_API: 'http://t2v-transformers:8080'

t2v-transformers:
  image: semitechnologies/transformers-inference:sentence-transformers-multi-qa-MiniLM-L6-cos-v1
  environment:
    ENABLE_CUDA: '0'
```

2. **Update your DocuCrawler code**

You'll need to modify the Weaviate connector to use the built-in vectorization instead of providing vectors directly.

## Troubleshooting

- **Connection issues**: Ensure Weaviate is running and accessible on the specified port.
- **Authentication errors**: Check your API key if authentication is enabled.
- **Schema errors**: If you're seeing schema-related errors, you may need to delete and recreate the class.
- **Memory issues**: Weaviate requires significant memory. If it's failing, try increasing the allocated memory.