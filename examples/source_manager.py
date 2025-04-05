#!/usr/bin/env python3
"""
CLI tool for managing documentation sources in DocuCrawler.
"""

import os
import json
import argparse
from typing import Dict, Any, List, Optional

CONFIG_FILE = 'sources.json'

def load_sources() -> Dict[str, Dict[str, Any]]:
    """Load sources from the configuration file.
    
    Returns:
        Dictionary of source configurations
    """
    if not os.path.exists(CONFIG_FILE):
        return {}
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading sources: {e}")
        return {}

def save_sources(sources: Dict[str, Dict[str, Any]]) -> None:
    """Save sources to the configuration file.
    
    Args:
        sources: Dictionary of source configurations
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(sources, file, indent=4)
        print(f"Sources saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving sources: {e}")

def list_sources(sources: Dict[str, Dict[str, Any]]) -> None:
    """List all configured sources.
    
    Args:
        sources: Dictionary of source configurations
    """
    if not sources:
        print("No sources configured.")
        return
    
    print("Configured sources:")
    for name, config in sources.items():
        print(f"- {name}:")
        print(f"  Sitemap URL: {config.get('sitemap_url', 'N/A')}")
        print(f"  Base URL: {config.get('base_url', 'N/A')}")
        print(f"  Max Depth: {config.get('max_depth', 'N/A')}")
        print(f"  Output Directory: {config.get('output_dir', 'N/A')}")
        print()

def add_source(sources: Dict[str, Dict[str, Any]], name: str, sitemap_url: str, 
               base_url: str, max_depth: int) -> None:
    """Add a new source configuration.
    
    Args:
        sources: Dictionary of source configurations
        name: Source name
        sitemap_url: URL of the sitemap
        base_url: Base URL for filtering
        max_depth: Maximum depth of links to include
    """
    if name in sources:
        print(f"Source '{name}' already exists. Use 'update' to modify it.")
        return
    
    output_dir = os.path.join('docs', 'crawled', name)
    
    sources[name] = {
        'sitemap_url': sitemap_url,
        'base_url': base_url,
        'max_depth': max_depth,
        'output_dir': output_dir,
        'max_concurrent': 10,
        'headless': True
    }
    
    save_sources(sources)
    print(f"Source '{name}' added successfully.")

def update_source(sources: Dict[str, Dict[str, Any]], name: str, 
                  sitemap_url: Optional[str] = None, base_url: Optional[str] = None, 
                  max_depth: Optional[int] = None) -> None:
    """Update an existing source configuration.
    
    Args:
        sources: Dictionary of source configurations
        name: Source name
        sitemap_url: URL of the sitemap (optional)
        base_url: Base URL for filtering (optional)
        max_depth: Maximum depth of links to include (optional)
    """
    if name not in sources:
        print(f"Source '{name}' does not exist. Use 'add' to create it.")
        return
    
    if sitemap_url:
        sources[name]['sitemap_url'] = sitemap_url
    
    if base_url:
        sources[name]['base_url'] = base_url
    
    if max_depth is not None:
        sources[name]['max_depth'] = max_depth
    
    save_sources(sources)
    print(f"Source '{name}' updated successfully.")

def remove_source(sources: Dict[str, Dict[str, Any]], name: str) -> None:
    """Remove a source configuration.
    
    Args:
        sources: Dictionary of source configurations
        name: Source name
    """
    if name not in sources:
        print(f"Source '{name}' does not exist.")
        return
    
    del sources[name]
    save_sources(sources)
    print(f"Source '{name}' removed successfully.")

def export_sources_to_main(sources: Dict[str, Dict[str, Any]]) -> None:
    """Export source configurations to main.py.
    
    Args:
        sources: Dictionary of source configurations
    """
    if not sources:
        print("No sources to export.")
        return
    
    source_names = list(sources.keys())
    
    print("To use these sources in main.py, update the following sections:")
    
    print("\n1. Add source names to the 'sources' list in setup_directories():")
    print(f"    sources = {source_names}")
    
    print("\n2. Update the connectors dictionary in run_crawl_step():")
    print("    connectors = {")
    for name in source_names:
        connector_class = f"{name.capitalize()}Connector"
        print(f"        '{name}': {connector_class}(),")
    print("    }")
    
    print("\n3. Create connector classes in docucrawler/crawlers/connectors.py:")
    for name in source_names:
        config = sources[name]
        connector_class = f"{name.capitalize()}Connector"
        print(f"""
class {connector_class}(WebCrawler):
    \"\"\"Connector for {name} documentation.\"\"\"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        \"\"\"Initialize the {name} connector.\"\"\"
        if config is None:
            config = {{}}
        
        default_config = {{
            'sitemap_url': '{config['sitemap_url']}',
            'base_url': '{config['base_url']}',
            'max_depth': {config['max_depth']},
            'output_dir': 'docs/crawled/{name}',
            'headless': True,
            'max_concurrent': 10
        }}
        
        merged_config = {{**default_config, **config}}
        super().__init__(merged_config)
        
        self.sitemap_url = merged_config['sitemap_url']
        self.base_url = merged_config['base_url']
        self.max_depth = merged_config['max_depth']
        self.output_dir = merged_config['output_dir']
    
    async def crawl_documentation(self) -> List[str]:
        \"\"\"Crawl {name} documentation.\"\"\"
        print(f"Fetching URLs from {name} sitemap: {{self.sitemap_url}}")
        urls = await self.get_urls(self.sitemap_url, self.base_url, self.max_depth)
        
        if not urls:
            print("No {name} URLs found or sitemap inaccessible.")
            return []
        
        print(f"Found {{len(urls)}} {name} URLs to crawl.")
        return await self.crawl(urls, self.output_dir)
""")

def main():
    """Run the source manager CLI."""
    parser = argparse.ArgumentParser(description='DocuCrawler Source Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    subparsers.add_parser('list', help='List all configured sources')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new source')
    add_parser.add_argument('name', help='Source name')
    add_parser.add_argument('sitemap_url', help='URL of the sitemap')
    add_parser.add_argument('base_url', help='Base URL for filtering')
    add_parser.add_argument('--max-depth', type=int, default=3, help='Maximum depth of links to include')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update an existing source')
    update_parser.add_argument('name', help='Source name')
    update_parser.add_argument('--sitemap-url', help='URL of the sitemap')
    update_parser.add_argument('--base-url', help='Base URL for filtering')
    update_parser.add_argument('--max-depth', type=int, help='Maximum depth of links to include')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a source')
    remove_parser.add_argument('name', help='Source name')
    
    # Export command
    subparsers.add_parser('export', help='Export sources to main.py')
    
    args = parser.parse_args()
    
    # Load sources
    sources = load_sources()
    
    if args.command == 'list':
        list_sources(sources)
    elif args.command == 'add':
        add_source(sources, args.name, args.sitemap_url, args.base_url, args.max_depth)
    elif args.command == 'update':
        update_source(sources, args.name, args.sitemap_url, args.base_url, args.max_depth)
    elif args.command == 'remove':
        remove_source(sources, args.name)
    elif args.command == 'export':
        export_sources_to_main(sources)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()