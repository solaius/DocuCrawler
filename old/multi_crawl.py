import os
import psutil
import asyncio
import requests
from xml.etree import ElementTree
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Directory for storing crawled content
OUTPUT_DIR = os.path.join(os.getcwd(), "LangChain Docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_docs_urls(sitemap_url: str, docs_base_url: str) -> List[str]:
    """Fetch URLs from a sitemap that start with the specified documentation base URL and are at most 2 directories deep."""
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()

        # Parse the XML content
        root = ElementTree.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Extract URLs starting with the documentation base URL and at most 2 directories deep
        urls = [
            loc.text for loc in root.findall('.//ns:loc', namespace)
            if loc.text.startswith(docs_base_url) and len(loc.text[len(docs_base_url):].strip('/').split('/')) <= 2
        ]
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []


async def crawl_parallel(urls: List[str], max_concurrent: int = 5):
    """Crawl multiple URLs in parallel and save their content."""
    print("\n=== Parallel Crawling ===")

    # Keep track of peak memory usage
    peak_memory = 0
    process = psutil.Process(os.getpid())

    def log_memory(prefix: str = ""):
        nonlocal peak_memory
        current_mem = process.memory_info().rss
        if current_mem > peak_memory:
            peak_memory = current_mem
        print(f"{prefix} Current Memory: {current_mem // (1024 * 1024)} MB, Peak: {peak_memory // (1024 * 1024)} MB")

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
        # Process URLs in chunks for parallel execution
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = [crawler.arun(url=url, config=crawl_config) for url in batch]

            # Log memory before starting the batch
            log_memory(prefix=f"Before batch {i // max_concurrent + 1}: ")

            # Execute the tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log memory after batch completion
            log_memory(prefix=f"After batch {i // max_concurrent + 1}: ")

            # Save the results
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                elif result.success:
                    # Save content to file
                    filename = os.path.join(OUTPUT_DIR, f"{url.split('/')[-2]}.txt")
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(result.markdown)
                    print(f"Saved: {filename}")
                else:
                    print(f"Failed to crawl {url}")

        print(f"\nAll tasks completed. Peak memory usage: {peak_memory // (1024 * 1024)} MB")

    finally:
        await crawler.close()

async def main():
    # Sitemap and docs base URL
    sitemap_url = "https://python.langchain.com/sitemap.xml"
    docs_base_url = "https://python.langchain.com/docs/"

    # Fetch the documentation URLs
    urls = get_docs_urls(sitemap_url, docs_base_url)
    if urls:
        print(f"Found {len(urls)} URLs to crawl.")
        await crawl_parallel(urls, max_concurrent=10)
    else:
        print("No URLs found to crawl.")

if __name__ == "__main__":
    asyncio.run(main())
