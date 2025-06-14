# SearchIQ

SearchIQ is a powerful natural language interface for Elasticsearch that allows users to query their Elasticsearch indices using natural language. It combines the capabilities of Elasticsearch with the power of LLMs (Large Language Models) to provide an intuitive search experience.

## Features

- Natural language querying of Elasticsearch indices
- Automatic index discovery and mapping analysis
- Flexible search capabilities with JSON query support
- Configurable search parameters and limits
- Comprehensive error handling and logging
- Secure connection handling with authentication support

## Prerequisites

- Python 3.8 or higher
- Elasticsearch server (local or remote)
- Ollama with Gemma 2B model (or other supported models)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SearchIQ.git
cd SearchIQ
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your configuration:
```env
ES_HOST=http://localhost:9200
ES_USERNAME=your_username
ES_PASSWORD=your_password
ES_VERIFY_CERTS=true
ES_TIMEOUT=30
DEFAULT_SEARCH_SIZE=5
MAX_SEARCH_SIZE=100
OLLAMA_MODEL=gemma:2b
```

## Usage

1. Start your Elasticsearch server
2. Start Ollama with the required model:
```bash
ollama run gemma:2b
```

3. Run the search interface:
```bash
python search/nl_search.py
```

4. Example queries:
```python
# List all Nobel laureates
ask_agent("Show me name of all nobel laureates from nobel-laureates index")

# Search with specific criteria
ask_agent("Find all Nobel laureates from the year 2020")

# Get specific fields
ask_agent("Show me the names and categories of all Nobel laureates")
```

## Project Structure

```
SearchIQ/
├── search/
│   └── nl_search.py    # Main search interface
├── .env                # Configuration file
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Configuration

The following environment variables can be configured in the `.env` file:

- `ES_HOST`: Elasticsearch server URL
- `ES_USERNAME`: Elasticsearch username (optional)
- `ES_PASSWORD`: Elasticsearch password (optional)
- `ES_VERIFY_CERTS`: Whether to verify SSL certificates
- `ES_TIMEOUT`: Request timeout in seconds
- `DEFAULT_SEARCH_SIZE`: Default number of results per query
- `MAX_SEARCH_SIZE`: Maximum number of results per query
- `OLLAMA_MODEL`: Name of the Ollama model to use

## Search Capabilities

The interface supports various types of Elasticsearch queries:

1. Match All Query:
```json
{"match_all": {}}
```

2. Field-specific Match:
```json
{"match": {"field": "value"}}
```

3. Source Filtering:
```json
{"_source": ["field1", "field2"]}
```

## Error Handling

The system includes comprehensive error handling for:
- Connection issues
- Invalid queries
- Missing indices
- Authentication failures
- Timeout errors

All errors are logged with appropriate context for debugging.

## Example Responses

The system provides well-formatted responses with clear structure. Here's an example of how the output looks:

```
=== Agent Response ===

The names of all Nobel laureates from the "nobel-laureates" index are:

- Albert Einstein
- Marie Curie
- Nelson Mandela
- Vaclav Havel
- Desmond Tutu
```

The system follows these response patterns:
1. Clear section headers with `=== Agent Response ===`
2. Natural language summary of the results
3. Formatted list of results when applicable
4. Error messages with clear explanations when something goes wrong

### Response Types

1. **List Results**:
```
The names of all Nobel laureates from the "nobel-laureates" index are:
- Item 1
- Item 2
- Item 3
```

2. **Search Results with Metadata**:
```json
{
  "total": 24,
  "took": 5,
  "results": [
    {
      "name": "Albert Einstein",
      "year": 1921,
      "category": "Physics"
    }
  ]
}
```

3. **Error Responses**:
```
Error: Index 'non-existent-index' does not exist
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Elasticsearch for the powerful search capabilities
- Ollama for providing the LLM capabilities
- LangChain for the agent framework 