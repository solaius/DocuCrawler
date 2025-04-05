import os
import asyncio
import requests
import psutil
from xml.etree import ElementTree
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

def ensure_directory_exists(directory):
    """Ensure a directory exists."""
    os.makedirs(directory, exist_ok=True)

def get_output_path(base_dir, sub_dir):
    """Create and return a structured path for crawled documents."""
    path = os.path.join(base_dir, sub_dir)
    ensure_directory_exists(path)
    return path

def get_urls_from_sitemap(sitemap_url, docs_base_url, max_depth=3):
    """Extract URLs from a sitemap and filter by base URL and depth."""
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()

        # Parse XML content
        root = ElementTree.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [
            loc.text for loc in root.findall('.//ns:loc', namespace)
            if loc.text.startswith(docs_base_url)
            and len(loc.text[len(docs_base_url):].strip('/').split('/')) <= max_depth
        ]
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def log_memory_usage(prefix=""):
    """Log current and peak memory usage."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    current_memory = memory_info.rss // (1024 * 1024)  # Convert to MB
    print(f"{prefix} Current Memory Usage: {current_memory} MB")

async def crawl_parallel(urls, output_dir, max_concurrent=10):
    """Crawl multiple URLs in parallel and save their content."""
    # Configure the crawler
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            tasks = [crawler.arun(url=url, config=crawl_config) for url in batch]

            log_memory_usage(prefix=f"Before batch {i // max_concurrent + 1}: ")

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                elif result.success:
                    filename = os.path.join(output_dir, f"{url.split('/')[-2]}.txt")
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(result.markdown_v2.raw_markdown)
                    print(f"Crawled and saved: {url}")
                else:
                    print(f"Failed to crawl {url}: {result.error_message}")

            log_memory_usage(prefix=f"After batch {i // max_concurrent + 1}: ")
    finally:
        await crawler.close()

async def main():
    base_dir = 'docs/crawled'

    # Define subdirectories for outputs
    langchain_dir = get_output_path(base_dir, 'langchain')
    docling_dir = get_output_path(base_dir, 'docling')

    # Define base URLs
    langchain_docs_base_url = "https://python.langchain.com/docs/"
    docling_docs_base_url = "https://ds4sd.github.io/docling/"

    # Fetch URLs from sitemaps
    langchain_sitemap = "https://python.langchain.com/sitemap.xml"
    docling_sitemap = "https://ds4sd.github.io/docling/sitemap.xml"

    langchain_urls = get_urls_from_sitemap(langchain_sitemap, langchain_docs_base_url, max_depth=2)
    docling_urls = get_urls_from_sitemap(docling_sitemap, docling_docs_base_url, max_depth=2)

    # Crawl and save documents for each category
    if langchain_urls:
        await crawl_parallel(langchain_urls, langchain_dir, max_concurrent=10)
    else:
        print("No LangChain URLs found.")

    if docling_urls:
        await crawl_parallel(docling_urls, docling_dir, max_concurrent=10)
    else:
        print("No Docling URLs found or sitemap inaccessible.")

if __name__ == "__main__":
    asyncio.run(main())
