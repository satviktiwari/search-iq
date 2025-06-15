import json
import logging
import time
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from functools import lru_cache
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError, ConnectionError, NotFoundError
from langchain.agents import initialize_agent, Tool
from langchain_community.llms import Ollama
from dotenv import load_dotenv
import os
import backoff
from datetime import datetime
import hashlib

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('searchiq.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ElasticSearchConfig:
    def __init__(self):
        self.host = os.getenv('ES_HOST', 'http://localhost:9200')
        self.username = os.getenv('ES_USERNAME')
        self.password = os.getenv('ES_PASSWORD')
        self.verify_certs = os.getenv('ES_VERIFY_CERTS', 'true').lower() == 'true'
        self.timeout = int(os.getenv('ES_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('ES_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('ES_RETRY_DELAY', '1'))

class SearchConfig:
    def __init__(self):
        self.default_size = int(os.getenv('DEFAULT_SEARCH_SIZE', '5'))
        self.max_size = int(os.getenv('MAX_SEARCH_SIZE', '100'))
        self.model_name = os.getenv('OLLAMA_MODEL', 'gemma:2b')
        self.cache_ttl = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes default
        self.max_cache_size = int(os.getenv('MAX_CACHE_SIZE', '1000'))

class QueryValidator:
    @staticmethod
    def validate_query_structure(query: Dict) -> Tuple[bool, str]:
        """Validate the structure of an Elasticsearch query."""
        if not isinstance(query, dict):
            return False, "Query must be a dictionary"
        
        # Check for common query types
        valid_query_types = {'match', 'match_all', 'term', 'terms', 'range', 'bool', '_source'}
        query_keys = set(query.keys())
        
        if not any(key in valid_query_types for key in query_keys):
            return False, f"Query must contain at least one valid query type: {valid_query_types}"
        
        return True, ""

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove any potential command injection characters
        return ''.join(c for c in input_str if c.isprintable())

class CacheManager:
    def __init__(self, ttl: int, max_size: int):
        self.ttl = ttl
        self.max_size = max_size
        self.cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and is not expired."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set a value in cache with timestamp."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        self.cache[key] = (value, time.time())

# Initialize configurations
es_config = ElasticSearchConfig()
search_config = SearchConfig()
cache_manager = CacheManager(search_config.cache_ttl, search_config.max_cache_size)

# Initialize ElasticSearch client with retry mechanism
@backoff.on_exception(
    backoff.expo,
    (ConnectionError, RequestError),
    max_tries=es_config.max_retries,
    max_time=30
)
def get_elasticsearch_client() -> Elasticsearch:
    """Initialize Elasticsearch client with retry mechanism."""
    try:
        client = Elasticsearch(
            es_config.host,
            basic_auth=(es_config.username, es_config.password) if es_config.username and es_config.password else None,
            verify_certs=es_config.verify_certs,
            timeout=es_config.timeout
        )
        if not client.ping():
            raise ConnectionError("Failed to connect to Elasticsearch")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Elasticsearch client: {str(e)}")
        raise

es = get_elasticsearch_client()

# Initialize Ollama LLM wrapper
llm = Ollama(model=search_config.model_name)

@lru_cache(maxsize=100)
def validate_index(index: str) -> bool:
    """Validate if an index exists with caching."""
    try:
        return es.indices.exists(index=index)
    except (RequestError, ConnectionError) as e:
        logger.error(f"Error validating index {index}: {str(e)}")
        return False

def generate_cache_key(index: str, query: Dict, size: int) -> str:
    """Generate a unique cache key for a search query."""
    query_str = json.dumps(query, sort_keys=True)
    return hashlib.md5(f"{index}:{query_str}:{size}".encode()).hexdigest()

def list_indices() -> str:
    """List all indices in ElasticSearch with additional metadata and caching."""
    cache_key = "list_indices"
    cached_result = cache_manager.get(cache_key)
    if cached_result:
        return cached_result

    try:
        indices = es.indices.get_alias("*")
        result = {}
        for index in indices:
            stats = es.indices.stats(index=index)
            result[index] = {
                "document_count": stats["indices"][index]["total"]["docs"]["count"],
                "size_in_bytes": stats["indices"][index]["total"]["store"]["size_in_bytes"],
                "last_updated": datetime.fromtimestamp(
                    stats["indices"][index]["total"]["refresh"]["total_time_in_millis"] / 1000
                ).isoformat()
            }
        result_str = json.dumps(result, indent=2)
        cache_manager.set(cache_key, result_str)
        return result_str
    except (RequestError, ConnectionError) as e:
        logger.error(f"Error listing indices: {str(e)}")
        return f"Error listing indices: {str(e)}"

def get_index_mappings(index: str) -> str:
    """Get mappings and settings of a specific index with validation."""
    index = QueryValidator.sanitize_input(index)
    try:
        if not validate_index(index):
            return f"Index '{index}' does not exist"
        
        mappings = es.indices.get_mapping(index=index)
        settings = es.indices.get_settings(index=index)
        
        result = {
            "mappings": mappings,
            "settings": settings,
            "last_updated": datetime.now().isoformat()
        }
        return json.dumps(result, indent=2)
    except (RequestError, ConnectionError, NotFoundError) as e:
        logger.error(f"Error getting mappings for index '{index}': {str(e)}")
        return f"Error getting mappings for index '{index}': {str(e)}"

def search_index(input_str: str) -> str:
    """Enhanced search functionality with validation, caching, and better error handling."""
    try:
        parts = input_str.split('|', 2)
        index = QueryValidator.sanitize_input(parts[0].strip())
        
        if not validate_index(index):
            return f"Index '{index}' does not exist"
        
        # Parse and validate query
        query = parts[1].strip() if len(parts) > 1 and parts[1].strip() else '{"match_all": {}}'
        try:
            query_dict = json.loads(query)
            is_valid, error_msg = QueryValidator.validate_query_structure(query_dict)
            if not is_valid:
                return f"Invalid query structure: {error_msg}"
        except json.JSONDecodeError:
            return "Invalid JSON query. Please provide a valid JSON string."
        
        # Parse size with validation
        size = search_config.default_size
        if len(parts) > 2 and parts[2].strip().isdigit():
            requested_size = int(parts[2].strip())
            size = min(requested_size, search_config.max_size)
        
        # Check cache
        cache_key = generate_cache_key(index, query_dict, size)
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Execute search with timeout and retry
        @backoff.on_exception(
            backoff.expo,
            (RequestError, ConnectionError),
            max_tries=es_config.max_retries
        )
        def execute_search():
            return es.search(
                index=index,
                query=query_dict,
                size=size,
                timeout=f"{es_config.timeout}s"
            )
        
        resp = execute_search()
        
        # Process results
        hits = resp.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        results = [hit["_source"] for hit in hits.get("hits", [])]
        
        result = {
            "total": total,
            "took": resp.get("took"),
            "results": results,
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }
        
        result_str = json.dumps(result, indent=2)
        cache_manager.set(cache_key, result_str)
        return result_str
        
    except (RequestError, ConnectionError, NotFoundError) as e:
        logger.error(f"Error searching index '{index}': {str(e)}")
        return f"Error searching index '{index}': {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error during search: {str(e)}")
        return f"Unexpected error: {str(e)}"

# Define enhanced LangChain tools
tools = [
    Tool(
        name="ListIndices",
        func=lambda _: list_indices(),
        description="Lists all indices in the ElasticSearch cluster with document counts, sizes, and last update times. No input needed."
    ),
    Tool(
        name="GetIndexMappings",
        func=get_index_mappings,
        description="Gets the mappings, settings, and last update time of a specified ElasticSearch index. Input is the index name."
    ),
    Tool(
        name="SearchIndex",
        func=search_index,
        description=(
            "Searches an ElasticSearch index with enhanced features. Input format: 'index|query|size'. "
            "Query is a JSON string. Size is optional number of results to return (max 100). "
            "Returns total count, execution time, results, and cache status."
        )
    ),
]

# Initialize LangChain agent with improved configuration
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)

def ask_agent(question: str) -> str:
    """Enhanced agent interaction with better prompting and error handling."""
    question = QueryValidator.sanitize_input(question)
    prompt = (
        "You are an expert ElasticSearch assistant that helps users query and analyze their data.\n"
        "Follow these steps:\n"
        "1. First, list all available indices to understand the data structure\n"
        "2. For relevant indices, examine their mappings to understand the fields\n"
        "3. Construct appropriate search queries based on the user's question\n"
        "4. Execute searches and analyze the results\n"
        "5. Provide a clear, concise answer with relevant data\n\n"
        "When using tools:\n"
        "- Use ListIndices to see available data\n"
        "- Use GetIndexMappings to understand the data structure\n"
        "- Use SearchIndex with appropriate queries to get the data\n"
        "- For listing all records, use a match_all query\n"
        "- For specific fields, use field-specific queries\n"
        "- Always check the total count in search results\n"
        "- Format the final answer in a clear, readable way\n\n"
        "Example queries:\n"
        "- To list all records: 'index|{\"match_all\": {}}'\n"
        "- To search specific field: 'index|{\"match\": {\"field\": \"value\"}}'\n"
        "- To get specific fields: 'index|{\"_source\": [\"field1\", \"field2\"]}'\n\n"
        "When using SearchIndex:\n"
        "- First parameter is the index name\n"
        "- Second parameter is the JSON query\n"
        "- Third parameter (optional) is the number of results\n"
        "- Always use proper JSON formatting for queries\n\n"
        f"User question: {question}"
    )
    
    try:
        response = agent.run(prompt)
        logger.info("Agent successfully processed the question")
        return response
    except Exception as e:
        error_msg = f"Error processing question: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    # Example usage with error handling
    try:
        result = ask_agent("Show me total number of all nobel laureates from nobel-laureates index")
        print("\n=== Agent Response ===\n")
        print(result)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"An error occurred: {str(e)}")
