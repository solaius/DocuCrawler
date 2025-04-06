# Elasticsearch Setup Guide

This guide provides step-by-step instructions for setting up Elasticsearch with vector search capabilities for use with DocuCrawler.

## Prerequisites

- Docker (recommended for easy setup)
- 4GB+ of RAM available for Elasticsearch
- curl or similar tool for API testing

## Option 1: Using Docker (Recommended)

1. **Create a Docker Compose file for Elasticsearch**

Create a file named `docker-compose-elasticsearch.yml` with the following content:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.4
    container_name: docucrawler-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ulimits:
      memlock:
        soft: -1
        hard: -1

volumes:
  elasticsearch-data:
```

2. **Start the Elasticsearch container**

```bash
docker-compose -f docker-compose-elasticsearch.yml up -d
```

3. **Wait for Elasticsearch to start**

It may take a minute or two for Elasticsearch to fully start. You can check the logs with:

```bash
docker logs -f docucrawler-elasticsearch
```

4. **Verify the installation**

```bash
curl http://localhost:9200
```

You should see a JSON response with Elasticsearch version information.

5. **Update your DocuCrawler .env file**

```
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=docucrawler
ELASTICSEARCH_USER=
ELASTICSEARCH_PASSWORD=
```

## Option 2: Manual Installation

### Ubuntu/Debian

1. **Install Java**

```bash
sudo apt update
sudo apt install openjdk-17-jdk
```

2. **Import the Elasticsearch GPG key**

```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
```

3. **Add the Elasticsearch repository**

```bash
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
```

4. **Install Elasticsearch**

```bash
sudo apt update
sudo apt install elasticsearch
```

5. **Configure Elasticsearch**

Edit the configuration file:

```bash
sudo nano /etc/elasticsearch/elasticsearch.yml
```

Add or modify these settings:

```yaml
xpack.security.enabled: false
discovery.type: single-node
```

6. **Start Elasticsearch**

```bash
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
```

7. **Verify the installation**

```bash
curl http://localhost:9200
```

8. **Update your DocuCrawler .env file**

```
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=docucrawler
ELASTICSEARCH_USER=
ELASTICSEARCH_PASSWORD=
```

### macOS

1. **Install Elasticsearch using Homebrew**

```bash
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full
```

2. **Start Elasticsearch**

```bash
elasticsearch
```

3. **Verify the installation**

```bash
curl http://localhost:9200
```

4. **Update your DocuCrawler .env file**

```
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=docucrawler
ELASTICSEARCH_USER=
ELASTICSEARCH_PASSWORD=
```

### Windows

1. **Download Elasticsearch**

Download the Windows ZIP file from the [Elasticsearch website](https://www.elastic.co/downloads/elasticsearch).

2. **Extract the ZIP file**

Extract the contents to a directory of your choice.

3. **Configure Elasticsearch**

Edit the `config/elasticsearch.yml` file and add:

```yaml
xpack.security.enabled: false
discovery.type: single-node
```

4. **Start Elasticsearch**

Run `bin\elasticsearch.bat` from the extracted directory.

5. **Verify the installation**

Open a browser and navigate to `http://localhost:9200`.

6. **Update your DocuCrawler .env file**

```
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=docucrawler
ELASTICSEARCH_USER=
ELASTICSEARCH_PASSWORD=
```

## Enabling Security (Optional)

If you want to enable security:

1. **Generate passwords**

```bash
# For Docker
docker exec -it docucrawler-elasticsearch /usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto

# For manual installation
sudo /usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto
```

2. **Update configuration**

Edit the Elasticsearch configuration to enable security:

```yaml
xpack.security.enabled: true
```

3. **Update your DocuCrawler .env file**

```
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=docucrawler
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=<generated_password>
```

## Verifying the Setup

To verify that Elasticsearch is properly set up and working with DocuCrawler:

1. **Run the vector database test**

```bash
python examples/vector_search.py "test query" --db-type elasticsearch
```

If everything is set up correctly, you should see a successful connection message and search results (if you have already indexed some documents).

## Troubleshooting

- **Low memory**: Elasticsearch requires significant memory. If it's failing to start, try increasing the allocated memory.
- **Connection refused**: Ensure Elasticsearch is running and accessible on the specified port.
- **Authentication failed**: Check your username and password if security is enabled.
- **Version compatibility**: Ensure you're using a compatible version of Elasticsearch (8.x recommended).