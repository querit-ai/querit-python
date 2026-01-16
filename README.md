# Querit Content Retrieval Platform — Python SDK

The Querit Python SDK provides a convenient way to interact with the Querit Content Retrieval Platform. It offers:

- Simple search interface for content retrieval
- Type-annotated request/response models
- Error handling for API responses
- Support for various search parameters and filters

For the Querit Content Retrieval Platform, we provide a Python SDK (Querit SDK) that allows developers to easily integrate and use Querit's content search capabilities programmatically.

## Installation

### Requirements
- Python 3.7+
- pip package manager

### Install from PyPI
```bash
pip install querit
```

### Install from source
```bash
git clone https://github.com/querit-ai/querit-python.git
pip install -e .
```

### Verify Installation
```python
python3 -c "import querit; print(querit.__version__)"
```

## Quick Start

### Authentication
First, obtain your API key from the Querit platform.

### Basic Usage
```python
from querit import QueritClient
from querit.models.request import SearchRequest
from querit.errors import QueritError

# Initialize client
client = QueritClient(
    api_key="Bearer your_api_key_here",
    timeout=30  # Optional timeout in seconds
)

# Create search request
request = SearchRequest(
    query="chat",
    count=5,
    # Add more parameters as needed
)

try:
    # Execute search
    response = client.search(request)
    
    # Process results
    for item in response.results:
        print(f"Title: {item.title}")
        print(f"URL: {item.url}")
        print("-" * 50)
        
except QueritError as e:
    print(f"Search failed: {e}")

## Advanced Usage

### Customizing Search Requests
```python
from querit.models.request import SearchRequest

# Advanced search with filters
request = SearchRequest(
    query="machine learning",
    count=10,
    filters={
        "language": "english",
        "date_range": "d1"
    }
)
```

## Error Handling

The SDK provides specific error classes:
- `QueritAPIError`: API request failures
- `QueritAuthError`: Authentication failures
- `QueritValidationError`: Invalid request parameters

## Best Practices
1. Reuse client instances rather than creating new ones for each request
2. Set appropriate timeout values for your use case
3. Handle rate limiting by implementing retry logic
4. Cache frequently used search results when possible

For more examples, see the `examples/` directory in this repository.

# Contact
If you experience any problems while using Querit, please feel free to reach out to us at support@querit.ai. Our team is ready to assist you.
