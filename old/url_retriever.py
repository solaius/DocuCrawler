import requests
from xml.etree import ElementTree
from typing import List

def get_docs_urls(sitemap_url: str, docs_base_url: str) -> List[str]:
    """Fetch URLs from a sitemap that start with the specified documentation base URL.
    
    Args:
        sitemap_url (str): The URL of the sitemap to fetch.
        docs_base_url (str): The base URL for the documentation pages.
        
    Returns:
        List[str]: A list of URLs related to the documentation.
    """
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

# Example usage
if __name__ == "__main__":
    sitemap = "https://python.langchain.com/sitemap.xml"
    docs_base = "https://python.langchain.com/docs/"
    doc_urls = get_docs_urls(sitemap, docs_base)
    for url in doc_urls:
        print(url)
