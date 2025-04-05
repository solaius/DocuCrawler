from setuptools import setup, find_packages

setup(
    name="docucrawler",
    version="0.1.0",
    description="Documentation Aggregation System",
    author="DocuCrawler Team",
    author_email="docucrawler@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "psutil>=5.9.0",
        "python-dotenv>=0.20.0",
        "tiktoken>=0.3.0",
        "crawl4ai>=0.1.0",
    ],
    extras_require={
        "language_detection": ["langdetect>=1.0.9"],
    },
    entry_points={
        "console_scripts": [
            "docucrawler=main:main_cli",
        ],
    },
    python_requires=">=3.8",
)