import asyncio
import os
from crawl4ai import *
from xml.etree import ElementTree
import requests
from typing import List

def get_docs_urls(sitemap_url: str, docs_base_url: str) -> List[str]:
    """Fetch URLs from a sitemap that start with the specified documentation base URL."""
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()

        # Parse the XML content
        root = ElementTree.fromstring(response.content)

        # Define the namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Extract URLs that start with the documentation base URL
        urls = [
            loc.text for loc in root.findall('.//ns:loc', namespace)
            if loc.text.startswith(docs_base_url)
        ]

        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

async def main():
    # Create folder for storing the crawled documents
    folder_name = "LangChainDocs"
    os.makedirs(folder_name, exist_ok=True)

    # Fetch LangChain documentation URLs
    sitemap_url = "https://python.langchain.com/sitemap.xml"
    docs_base_url = "https://python.langchain.com/docs/"
    urls = get_docs_urls(sitemap_url, docs_base_url)

    if not urls:
        print("No URLs found in the sitemap.")
        return

    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                # Crawl each URL and get the content
                result = await crawler.arun(url=url)
                filename = os.path.join(folder_name, f"{url.split('/')[-2]}.txt")

                # Save the crawled content to a text file
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(result.markdown)
                print(f"Saved: {filename}")
            except Exception as e:
                print(f"Error crawling {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
