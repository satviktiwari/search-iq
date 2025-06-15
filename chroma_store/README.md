# Chroma Store Directory

This directory contains the Chroma vector database integration for SearchIQ, providing persistent storage and retrieval of vector embeddings.

## Purpose

- Persistent storage of vector embeddings
- Efficient similarity search
- Vector database management
- Integration with SearchIQ

## Components

### Vector Storage
- Chroma database configuration
- Collection management
- Vector persistence
- Index optimization

### Search Operations
- Similarity search
- Metadata filtering
- Batch operations
- Query optimization

### Data Management
- Collection creation
- Data migration
- Backup procedures
- Cleanup operations

## Usage

```python
from chroma_store.client import get_chroma_client
from chroma_store.collections import create_collection

# Initialize client
client = get_chroma_client()

# Create collection
collection = create_collection("documents")

# Add vectors
collection.add(
    embeddings=[[1.0, 2.0, 3.0]],
    documents=["Sample document"],
    metadatas=[{"source": "test"}]
)

# Query vectors
results = collection.query(
    query_embeddings=[[1.0, 2.0, 3.0]],
    n_results=5
)
```

## Configuration

The Chroma store can be configured through environment variables:
- `CHROMA_HOST`: Chroma server host
- `CHROMA_PORT`: Chroma server port
- `CHROMA_PERSIST_DIR`: Directory for persistent storage
- `CHROMA_COLLECTION_NAME`: Default collection name

## Best Practices

1. **Performance**
   - Use appropriate batch sizes
   - Optimize index settings
   - Monitor resource usage
   - Implement caching

2. **Data Management**
   - Regular backups
   - Data validation
   - Cleanup procedures
   - Version control

3. **Security**
   - Access control
   - Data encryption
   - Secure connections
   - Audit logging

## Directory Structure

```
chroma_store/
├── client.py         # Chroma client configuration
├── collections.py    # Collection management
├── operations.py     # Vector operations
└── utils.py         # Utility functions
```

## Contributing

When modifying Chroma store functionality:
1. Document new features
2. Add performance tests
3. Update configuration
4. Update this README 