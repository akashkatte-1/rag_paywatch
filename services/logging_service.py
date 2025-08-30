import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class LoggingService:
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the logging service.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration with both file and console handlers."""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            self.log_dir / f"rag_app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for simple logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Configure root logger
        self.logger = logging.getLogger('rag_app')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
        
    def log_query(self, query: str, user_id: Optional[str] = None, 
                  api_key_hash: Optional[str] = None, additional_data: Optional[Dict[str, Any]] = None):
        """
        Log a user query.
        
        Args:
            query: The user's query text
            user_id: Optional user identifier
            api_key_hash: Optional hashed API key for tracking
            additional_data: Additional data to log
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "user_query",
            "query": query,
            "user_id": user_id,
            "api_key_hash": api_key_hash,
            "additional_data": additional_data or {}
        }
        
        self.logger.info(f"User Query: {query}")
        self._write_structured_log(log_data, "queries")
        
    def log_rag_response(self, query: str, response: str, 
                        processing_time: Optional[float] = None,
                        user_id: Optional[str] = None,
                        api_key_hash: Optional[str] = None,
                        additional_data: Optional[Dict[str, Any]] = None):
        """
        Log a RAG response.
        
        Args:
            query: The original user query
            response: The RAG system response
            processing_time: Time taken to process the query (in seconds)
            user_id: Optional user identifier
            api_key_hash: Optional hashed API key for tracking
            additional_data: Additional data to log
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "rag_response",
            "query": query,
            "response": response,
            "processing_time_seconds": processing_time,
            "user_id": user_id,
            "api_key_hash": api_key_hash,
            "additional_data": additional_data or {}
        }
        
        self.logger.info(f"RAG Response: {response[:100]}..." if len(response) > 100 else f"RAG Response: {response}")
        self._write_structured_log(log_data, "responses")
        
    def log_file_upload(self, filename: str, file_size: int, 
                       success: bool, error_message: Optional[str] = None,
                       user_id: Optional[str] = None,
                       api_key_hash: Optional[str] = None):
        """
        Log file upload events.
        
        Args:
            filename: Name of the uploaded file
            file_size: Size of the file in bytes
            success: Whether the upload was successful
            error_message: Error message if upload failed
            user_id: Optional user identifier
            api_key_hash: Optional hashed API key for tracking
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "file_upload",
            "filename": filename,
            "file_size_bytes": file_size,
            "success": success,
            "error_message": error_message,
            "user_id": user_id,
            "api_key_hash": api_key_hash
        }
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"File Upload {status}: {filename} ({file_size} bytes)")
        self._write_structured_log(log_data, "uploads")
        
    def log_error(self, error_message: str, error_type: str = "general",
                  user_id: Optional[str] = None,
                  api_key_hash: Optional[str] = None,
                  additional_data: Optional[Dict[str, Any]] = None):
        """
        Log error events.
        
        Args:
            error_message: The error message
            error_type: Type of error (e.g., 'api_error', 'processing_error')
            user_id: Optional user identifier
            api_key_hash: Optional hashed API key for tracking
            additional_data: Additional error data
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "user_id": user_id,
            "api_key_hash": api_key_hash,
            "additional_data": additional_data or {}
        }
        
        self.logger.error(f"Error ({error_type}): {error_message}")
        self._write_structured_log(log_data, "errors")
        
    def _write_structured_log(self, log_data: Dict[str, Any], log_type: str):
        """
        Write structured log data to JSON file.
        
        Args:
            log_data: The log data to write
            log_type: Type of log (queries, responses, uploads, errors)
        """
        log_file = self.log_dir / f"{log_type}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write structured log: {e}")
            
    def get_logs_by_date(self, date: str, log_type: str = "all") -> list:
        """
        Retrieve logs for a specific date.
        
        Args:
            date: Date in YYYYMMDD format
            log_type: Type of logs to retrieve (queries, responses, uploads, errors, all)
            
        Returns:
            List of log entries
        """
        logs = []
        
        if log_type == "all":
            log_types = ["queries", "responses", "uploads", "errors"]
        else:
            log_types = [log_type]
            
        for log_type_name in log_types:
            log_file = self.log_dir / f"{log_type_name}_{date}.jsonl"
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                logs.append(json.loads(line.strip()))
                except Exception as e:
                    self.logger.error(f"Failed to read log file {log_file}: {e}")
                    
        return sorted(logs, key=lambda x: x.get('timestamp', ''))
