# Uploads Directory

This directory serves as a temporary storage location for user-uploaded files in SearchIQ. It handles file uploads, processing, and temporary storage before data is indexed in Elasticsearch.

## Purpose

- Temporary storage for user uploads
- File processing and validation
- Data extraction and preparation
- Cleanup of processed files

## File Types

The directory supports various file types:
- Text files (.txt, .md, .rst)
- Documents (.pdf, .doc, .docx)
- Spreadsheets (.csv, .xlsx)
- Other supported formats

## Usage Guidelines

1. **File Upload**
   - Files are temporarily stored here
   - Automatic cleanup after processing
   - Size limits apply
   - Format validation

2. **Processing**
   - Files are processed in order
   - Extracted data is indexed
   - Original files are cleaned up
   - Error handling for invalid files

3. **Security**
   - File type validation
   - Size restrictions
   - Malware scanning
   - Access control

## Best Practices

1. **File Management**
   - Regular cleanup of old files
   - Proper error handling
   - Logging of operations
   - Backup procedures

2. **Security**
   - Validate file types
   - Scan for malware
   - Implement size limits
   - Control access

3. **Performance**
   - Efficient processing
   - Resource management
   - Queue management
   - Error recovery

## Directory Structure

```
uploads/
├── temp/           # Temporary storage
├── processed/      # Successfully processed files
├── failed/         # Failed uploads
└── logs/           # Upload logs
```

## Contributing

When modifying upload functionality:
1. Update security measures
2. Document new file types
3. Add validation rules
4. Update this README 