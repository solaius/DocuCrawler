#!/usr/bin/env python3
"""
Test script for DocuCrawler's document processing functionality.
"""

import os
import asyncio
from dotenv import load_dotenv

from docucrawler.processors.markdown_processor import MarkdownProcessor
from docucrawler.utils.common import ensure_directory_exists, save_text

# Load environment variables
load_dotenv()

async def create_test_documents():
    """Create test markdown documents for processing."""
    test_dir = os.path.join('docs', 'test', 'markdown')
    ensure_directory_exists(test_dir)
    
    # Create a test markdown document
    test_doc = """# Test Document Title

This is a test document for the markdown processor.

## Section 1

This section contains some text and a [link to example](https://example.com).

* List item 1
* List item 2
* List item 3

## Section 2

This section contains a code block:

```python
def hello_world():
    print("Hello, world!")
```

And an image:

![Example Image](https://example.com/image.png)

## Section 3

This section has some more text with **bold** and *italic* formatting.

---

### Subsection

More content here...
"""
    
    # Save the test document
    test_file = os.path.join(test_dir, 'test_document.md')
    save_text(test_file, test_doc)
    
    return test_dir, [test_file]

async def test_markdown_processor():
    """Test the markdown processor."""
    print("=== Testing Markdown Processor ===")
    
    # Create test documents
    input_dir, test_files = await create_test_documents()
    print(f"Created test documents in {input_dir}")
    
    # Set up output directory
    output_dir = os.path.join('docs', 'test', 'processed')
    ensure_directory_exists(output_dir)
    
    # Create processor with custom configuration
    config = {
        'max_concurrent': 5,
        'summary_length': 150,
        'language_detection': False
    }
    
    processor = MarkdownProcessor(config)
    
    # Process a single document manually
    print("\nTesting single document processing:")
    with open(test_files[0], 'r', encoding='utf-8') as file:
        content = file.read()
    
    result = processor.process_document(content)
    print(f"Title: {result['title']}")
    print(f"Summary: {result['summary'][:50]}...")
    print(f"Content length: {result['metadata']['length']} characters")
    
    # Process all documents in the directory
    print("\nTesting directory processing:")
    processed_files = await processor.process(input_dir, output_dir)
    
    print(f"Successfully processed {len(processed_files)} files:")
    for file in processed_files:
        print(f"  - {file}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_markdown_processor())