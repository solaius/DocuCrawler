# Contributing to DocuCrawler

Thank you for your interest in contributing to DocuCrawler! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug in DocuCrawler, please report it by creating an issue on GitHub. When reporting a bug, please include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any error messages or logs
- Your environment (OS, Python version, etc.)

### Suggesting Features

If you have an idea for a new feature or enhancement, please create an issue on GitHub. When suggesting a feature, please include:

- A clear and descriptive title
- A detailed description of the feature
- Why the feature would be useful
- Any relevant examples or use cases

### Pull Requests

We welcome pull requests for bug fixes, features, documentation improvements, and other contributions. To submit a pull request:

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes
4. Write or update tests as needed
5. Ensure all tests pass
6. Submit a pull request

Please include a clear description of the changes and reference any related issues.

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/solaius/DocuCrawler.git
cd DocuCrawler
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install the package in development mode:

```bash
pip install -e .
```

## Coding Guidelines

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Write tests for new features and bug fixes
- Keep functions and methods focused on a single responsibility
- Use meaningful variable and function names

## Testing

Before submitting a pull request, please run the tests to ensure your changes don't break existing functionality:

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_crawlers.py
```

## Documentation

When adding new features or making significant changes, please update the documentation accordingly. This includes:

- Docstrings in the code
- README.md updates if needed
- Documentation files in the documentation directory

## Commit Messages

Write clear and meaningful commit messages that explain the purpose of your changes. Use the present tense and imperative mood (e.g., "Add feature" not "Added feature").

## Licensing

By contributing to DocuCrawler, you agree that your contributions will be licensed under the project's MIT License.

## Questions?

If you have any questions about contributing, please create an issue on GitHub or reach out to the maintainers.

Thank you for contributing to DocuCrawler!