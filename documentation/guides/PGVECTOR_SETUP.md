# PGVector Setup Guide

This guide provides step-by-step instructions for setting up PostgreSQL with the pgvector extension for use with DocuCrawler.

## Prerequisites

- Docker (recommended for easy setup)
- PostgreSQL client tools (optional, for direct database access)

## Option 1: Using Docker (Recommended)

1. **Create a Docker Compose file for PostgreSQL with pgvector**

Create a file named `docker-compose-pgvector.yml` with the following content:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: docucrawler-pgvector
    environment:
      POSTGRES_USER: devuser
      POSTGRES_PASSWORD: devuser
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgvector-data:/var/lib/postgresql/data
    command: postgres -c shared_preload_libraries=vector

volumes:
  pgvector-data:
```

2. **Start the PostgreSQL container**

```bash
docker-compose -f docker-compose-pgvector.yml up -d
```

3. **Verify the installation**

```bash
docker exec -it docucrawler-pgvector psql -U devuser -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT * FROM pg_extension WHERE extname = 'vector';"
```

You should see output confirming that the vector extension is installed.

4. **Update your DocuCrawler .env file**

```
PGVECTOR_URL=localhost:5432
PGVECTOR_DB=postgres
PGVECTOR_USER=devuser
PGVECTOR_PASSWORD=devuser
```

## Option 2: Manual Installation

### Ubuntu/Debian

1. **Install PostgreSQL**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-server-dev-all
```

2. **Install build dependencies**

```bash
sudo apt install git build-essential
```

3. **Clone and build pgvector**

```bash
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

4. **Configure PostgreSQL**

```bash
sudo -u postgres psql -c "CREATE USER devuser WITH PASSWORD 'devuser' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE postgres WITH OWNER devuser;"
sudo -u postgres psql -d postgres -c "CREATE EXTENSION vector;"
```

5. **Update your DocuCrawler .env file**

```
PGVECTOR_URL=localhost:5432
PGVECTOR_DB=postgres
PGVECTOR_USER=devuser
PGVECTOR_PASSWORD=devuser
```

### macOS

1. **Install PostgreSQL using Homebrew**

```bash
brew install postgresql
```

2. **Install pgvector**

```bash
brew install pgvector/brew/pgvector
```

3. **Start PostgreSQL**

```bash
brew services start postgresql
```

4. **Configure PostgreSQL**

```bash
psql postgres -c "CREATE USER devuser WITH PASSWORD 'devuser' SUPERUSER;"
psql postgres -c "CREATE DATABASE postgres WITH OWNER devuser;"
psql -d postgres -c "CREATE EXTENSION vector;"
```

5. **Update your DocuCrawler .env file**

```
PGVECTOR_URL=localhost:5432
PGVECTOR_DB=postgres
PGVECTOR_USER=devuser
PGVECTOR_PASSWORD=devuser
```

### Windows

1. **Install PostgreSQL**

Download and install PostgreSQL from the [official website](https://www.postgresql.org/download/windows/).

2. **Install pgvector**

- Download the pgvector release for your PostgreSQL version from [GitHub](https://github.com/pgvector/pgvector/releases).
- Extract the files to the PostgreSQL extension directory (typically `C:\Program Files\PostgreSQL\{version}\share\extension`).

3. **Configure PostgreSQL**

Open pgAdmin or the PostgreSQL command line tool and run:

```sql
CREATE USER devuser WITH PASSWORD 'devuser' SUPERUSER;
CREATE DATABASE postgres WITH OWNER devuser;
CREATE EXTENSION vector;
```

4. **Update your DocuCrawler .env file**

```
PGVECTOR_URL=localhost:5432
PGVECTOR_DB=postgres
PGVECTOR_USER=devuser
PGVECTOR_PASSWORD=devuser
```

## Verifying the Setup

To verify that PGVector is properly set up and working with DocuCrawler:

1. **Run the vector database test**

```bash
python examples/vector_search.py "test query" --db-type pgvector
```

If everything is set up correctly, you should see a successful connection message and search results (if you have already indexed some documents).

## Troubleshooting

- **Connection issues**: Ensure PostgreSQL is running and accessible on the specified port.
- **Extension not found**: Verify that the pgvector extension is properly installed.
- **Permission denied**: Check that the user has the necessary permissions to create tables and extensions.
- **Version compatibility**: Ensure you're using compatible versions of PostgreSQL and pgvector.