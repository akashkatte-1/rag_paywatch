import hashlib
import os
from typing import Optional

def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for logging purposes to maintain privacy.
    
    Args:
        api_key: The API key to hash
        
    Returns:
        Hashed version of the API key (first 8 characters)
    """
    if not api_key:
        return "none"
    
    # Create a hash of the API key
    hash_object = hashlib.sha256(api_key.encode())
    hash_hex = hash_object.hexdigest()
    
    # Return first 8 characters for identification while maintaining privacy
    return hash_hex[:8]

def extract_user_id_from_api_key(api_key: str) -> Optional[str]:
    """
    Extract a user identifier from the API key if it follows a specific pattern.
    This is optional and depends on your API key structure.
    
    Args:
        api_key: The API key
        
    Returns:
        User ID if found, None otherwise
    """
    # This is a placeholder implementation
    # You can customize this based on your API key structure
    # For example, if your API keys follow pattern: "user_123_abc123"
    
    if not api_key:
        return None
    
    # Example: extract user ID if API key contains "user_" prefix
    if "user_" in api_key:
        parts = api_key.split("_")
        if len(parts) >= 2:
            return parts[1]
    
    return None

def get_request_metadata(request_data: dict) -> dict:
    """
    Extract metadata from request data for logging.
    
    Args:
        request_data: Dictionary containing request information
        
    Returns:
        Dictionary with relevant metadata
    """
    metadata = {}
    
    # Extract file information if present
    if 'filename' in request_data:
        metadata['filename'] = request_data['filename']
    
    if 'file_size' in request_data:
        metadata['file_size'] = request_data['file_size']
    
    # Extract query information if present
    if 'query' in request_data:
        metadata['query_length'] = len(request_data['query'])
        metadata['query_type'] = 'text'
    
    return metadata
