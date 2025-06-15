# SearchIQ - PDF Semantic Search System

This project implements a semantic search system for PDF documents using Elasticsearch and sentence transformers. It allows you to index PDF content and perform semantic searches on the indexed content.

## Components

The project consists of two main Python scripts:

1. `hydrate_es.py` - Indexes PDF content into Elasticsearch
2. `search.py` - Performs semantic search queries on the indexed content

## Prerequisites

- Python 3.x
- Elasticsearch running locally (default: http://localhost:9200)
- Required Python packages:
  - PyMuPDF (fitz)
  - sentence-transformers
  - elasticsearch

## Installation

1. Install the required Python packages:
```bash
pip install PyMuPDF sentence-transformers elasticsearch
```

2. Ensure Elasticsearch is running locally on port 9200

## Usage

### 1. Indexing PDF Content

Run the hydration script to index your PDF content:
```bash
python hydrate_es.py
```

This script will:
- Create an Elasticsearch index named "aws-overview"
- Extract text from the PDF file
- Generate embeddings using the all-MiniLM-L6-v2 model
- Index the content and embeddings into Elasticsearch

### 2. Performing Semantic Search

Run the search script to query the indexed content:
```bash
python search.py
```

When prompted, enter your search query. The script will:
- Convert your query into an embedding
- Perform a semantic search using cosine similarity
- Display the top 3 most relevant matches with their scores

## Configuration

The following parameters can be modified in the scripts:

- `INDEX_NAME`: Name of the Elasticsearch index (default: "aws-overview")
- `ES_HOST`: Elasticsearch host URL (default: "http://localhost:9200")
- `VECTOR_DIM`: Dimension of the embedding vectors (default: 384)
- `PDF_PATH`: Path to the PDF file to be indexed

## Notes

- The system uses the all-MiniLM-L6-v2 model for generating embeddings
- Search results are ranked using cosine similarity
- The current implementation returns the top 3 matches for each query 