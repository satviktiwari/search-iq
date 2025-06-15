# SearchIQ - PDF Semantic Search System

This project implements a semantic search system for PDF documents using Elasticsearch and sentence transformers. It allows you to index PDF content and perform semantic searches on the indexed content through both a command-line interface and a web interface.

## Components

The project consists of several components:

1. Backend Scripts:
   - `hydrate_es.py` - Command-line tool to index PDF content into Elasticsearch
   - `search.py` - Command-line tool to perform semantic search queries

2. Web Interface (Frontend):
   - Flask-based web application (`frontend/app.py`)
   - HTML templates for upload, search, and results pages
   - Interactive web interface for PDF indexing and semantic search

## Prerequisites

- Python 3.x
- Elasticsearch running locally (default: http://localhost:9200)
- Required Python packages:
  - PyMuPDF (fitz)
  - sentence-transformers
  - elasticsearch
  - Flask (for web interface)

## Installation

1. Install the required Python packages:
```bash
pip install PyMuPDF sentence-transformers elasticsearch Flask
```

2. Ensure Elasticsearch is running locally on port 9200

## Usage

### Web Interface

1. Start the web application:
```bash
cd frontend
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Use the web interface to:
   - Upload and index PDF files
   - Perform semantic searches
   - View search results with relevance scores

### Command Line Interface

#### 1. Indexing PDF Content

Run the hydration script to index your PDF content:
```bash
python hydrate_es.py
```

This script will:
- Create an Elasticsearch index named "aws-overview"
- Extract text from the PDF file
- Generate embeddings using the all-MiniLM-L6-v2 model
- Index the content and embeddings into Elasticsearch

#### 2. Performing Semantic Search

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
- `UPLOAD_FOLDER`: Directory for storing uploaded PDFs (default: "frontend/uploads")

## Project Structure

```
.
├── frontend/
│   ├── app.py              # Flask web application
│   ├── requirements.txt    # Frontend dependencies
│   ├── templates/          # HTML templates
│   │   ├── upload.html    # PDF upload page
│   │   ├── search.html    # Search interface
│   │   └── results.html   # Search results page
│   └── uploads/           # Directory for uploaded PDFs
├── hydrate_es.py          # PDF indexing script
└── search.py             # Command-line search script
```

## Notes

- The system uses the all-MiniLM-L6-v2 model for generating embeddings
- Search results are ranked using cosine similarity
- The web interface returns the top 5 matches for each query
- The command-line interface returns the top 3 matches
- Index names are automatically sanitized to be Elasticsearch-compatible 