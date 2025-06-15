# Streamlit RAG App Directory

This directory contains the Streamlit-based web application for SearchIQ, implementing a Retrieval-Augmented Generation (RAG) interface for natural language search.

## Purpose

- Web interface for SearchIQ
- RAG implementation
- User interaction handling
- Search result visualization

## Components

### Web Interface
- Streamlit application
- User input handling
- Result display
- Error handling

### RAG Implementation
- Document retrieval
- Context generation
- Response synthesis
- Result ranking

### Search Integration
- Elasticsearch connection
- Vector search
- Hybrid search
- Result formatting

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Access the web interface at `http://localhost:8501`

3. Use the interface to:
   - Upload documents
   - Perform searches
   - View results
   - Export data

## Features

1. **Document Management**
   - File upload
   - Document processing
   - Index management
   - Version control

2. **Search Interface**
   - Natural language queries
   - Advanced filters
   - Result visualization
   - Export options

3. **RAG Capabilities**
   - Context-aware responses
   - Source attribution
   - Confidence scoring
   - Result explanation

## Configuration

The application can be configured through:
- Environment variables
- Configuration files
- UI settings
- Command-line arguments

## Best Practices

1. **User Experience**
   - Intuitive interface
   - Clear feedback
   - Error handling
   - Performance optimization

2. **Security**
   - Input validation
   - Access control
   - Data protection
   - Secure connections

3. **Maintenance**
   - Regular updates
   - Performance monitoring
   - Error logging
   - Backup procedures

## Directory Structure

```
streamlit_rag_app/
├── app.py           # Main application
├── components/      # UI components
├── utils/          # Utility functions
└── config/         # Configuration files
```

## Contributing

When modifying the RAG app:
1. Update documentation
2. Add new features
3. Improve UI/UX
4. Update this README 