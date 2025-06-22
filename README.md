# SearchIQ - Advanced Document Search System

SearchIQ is a powerful document search system that combines traditional text search with semantic search capabilities. It allows you to upload PDF documents and search through them using various advanced features.

## Features

### 1. Document Upload
- Upload PDF documents
- Automatic metadata extraction
- Section detection and indexing
- Reading time calculation
- Keyword extraction

### 2. Advanced Search Capabilities

#### Basic Search
- Simple text search across all documents
- Semantic search using natural language queries
- Combined text and semantic search

#### Advanced Search Operators
- **AND**: Find documents containing all specified terms
  ```
  machine AND learning
  ```
- **OR**: Find documents containing any of the specified terms
  ```
  python OR java
  ```
- **NOT**: Exclude documents containing specific terms
  ```
  programming NOT java
  ```

#### Filters
- **Date Range**: Filter documents by upload date
- **Document Type**: Filter by file type (PDF, DOC, TXT)
- **Section**: Search within specific sections of documents
- **Reading Time**: Filter by estimated reading time

#### Search History
- Save frequently used searches
- Quick access to previous searches
- Reuse search parameters

## How to Use

### 1. Uploading Documents
1. Navigate to the home page
2. Click "Choose File" to select a PDF document
3. Click "Upload" to process the document
4. Wait for the indexing process to complete

### 2. Searching Documents

#### Basic Search
1. Go to the Search page
2. Enter your search query in the "Search Query" field
3. Enter the index name (usually the name of your uploaded document)
4. Click "Search"

#### Advanced Search
1. Go to the Search page
2. Use the advanced search form to:
   - Enter a text query with operators (AND, OR, NOT)
   - Add an optional semantic query
   - Set date range filters
   - Select document type
   - Choose specific sections to search in
3. Click "Search"

#### Saving Searches
1. After performing a search, click "Save Search"
2. The search will appear in your search history
3. Click on any saved search to reuse its parameters

### 3. Understanding Results

Search results show:
- Relevance score
- Document title
- Author information
- Upload date
- File type
- Section information
- Reading time
- Relevant keywords
- Matching text excerpt

## Search Tips

1. **Combining Operators**
   ```
   (machine AND learning) NOT python
   ```

2. **Section-Specific Search**
   - Use the section dropdown to search within specific parts of documents
   - Useful for finding information in particular chapters or sections

3. **Date Filtering**
   - Use date range to find recently uploaded documents
   - Filter by creation or modification date

4. **Semantic Search**
   - Use natural language queries for concept-based search
   - Example: "What are the main points about machine learning?"
   - Works well with technical or complex topics

5. **Keyword Search**
   - Look for specific terms or phrases
   - Use quotes for exact phrase matching
   - Example: "neural network architecture"

## Technical Details

### Indexing Process
- Documents are split into sections
- Each section is indexed separately
- Metadata is extracted and stored
- Vector embeddings are generated for semantic search
- Keywords are extracted automatically

### Search Process
- Combines traditional text search with vector similarity
- Supports boolean operators
- Filters results based on metadata
- Ranks results by relevance

## Requirements

- Python 3.8+
- Elasticsearch 7.x
- Flask
- PyMuPDF
- Sentence Transformers

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start Elasticsearch
4. Run the application:
   ```bash
   python frontend/app.py
   ```

## Contributing

Feel free to submit issues and enhancement requests! 