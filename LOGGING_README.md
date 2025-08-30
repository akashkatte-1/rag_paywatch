# RAG Application Logging System

## Overview
The logging system tracks user queries, RAG responses, file uploads, and errors with privacy protection.

## Features
- 🔒 Privacy-first (API keys are hashed)
- 📊 Structured JSON logging
- 📈 Performance tracking
- 🔍 Easy analysis tools

## Usage

### 1. Automatic Logging
Logging is automatically integrated into your endpoints:
- `/upload-excel/` - Logs file uploads
- `/query/` - Logs queries and responses
- `/logs/` - Retrieve logs via API

### 2. Log Analysis
```bash
# View today's report
python log_analyzer.py

# View specific date
python log_analyzer.py --date 20241201

# List available dates
python log_analyzer.py --list-dates
```

### 3. API Log Retrieval
```bash
# Get all logs for today
curl -H "X-API-Key: your_api_key" "http://localhost:8000/logs/"

# Get specific log type
curl -H "X-API-Key: your_api_key" "http://localhost:8000/logs/?log_type=queries"
```

## Log Files
- `logs/queries_YYYYMMDD.jsonl` - User queries
- `logs/responses_YYYYMMDD.jsonl` - RAG responses  
- `logs/uploads_YYYYMMDD.jsonl` - File uploads
- `logs/errors_YYYYMMDD.jsonl` - Error events

## What Gets Logged
- User queries with metadata
- RAG responses with processing time
- File upload attempts and results
- All errors with categorization
- Performance metrics

## Privacy
- API keys are hashed (first 8 chars of SHA256)
- User IDs extracted from API key patterns
- No sensitive data stored in logs
