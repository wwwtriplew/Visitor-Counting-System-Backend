"""
Environment variable validation utilities.

This module provides functions to validate and load required environment
variables for the Visitor Counting System Backend. It ensures that all
necessary configuration is present and valid before the application runs.
"""

import os
import re
from typing import Dict, Optional
from urllib.parse import urlparse

from backend.config import (
    ENV_SUPABASE_URL,
    ENV_SUPABASE_SERVICE_KEY,
    ENV_YOLO_MODEL_PATH,
    ENV_TABLE_NAME,
    DEFAULT_YOLO_MODEL_PATH,
    DEFAULT_TABLE_NAME
)


class EnvironmentValidationError(Exception):
    """Raised when environment variable validation fails."""
    pass


def validate_url(url: str) -> bool:
    """
    Validate if a string is a properly formatted URL.
    
    Args:
        url: The URL string to validate.
        
    Returns:
        True if the URL is valid, False otherwise.
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def validate_supabase_key(key: str) -> bool:
    """
    Validate if a string looks like a valid Supabase key.
    
    Supabase keys are typically JWT tokens with a specific format.
    This performs basic validation to catch obvious errors.
    
    Args:
        key: The Supabase key to validate.
        
    Returns:
        True if the key appears valid, False otherwise.
    """
    if not key or len(key) < 20:
        return False
    
    # Supabase keys are typically long alphanumeric strings with dots and dashes
    # This is a basic check to ensure the key isn't obviously invalid
    return bool(re.match(r'^[A-Za-z0-9._-]+$', key))


def validate_environment() -> Dict[str, str]:
    """
    Validate and load all required environment variables.
    
    This function checks that all necessary environment variables are present
    and valid. It raises EnvironmentValidationError if any validation fails.
    
    Returns:
        Dictionary containing validated environment variables.
        
    Raises:
        EnvironmentValidationError: If any required environment variable is
            missing or invalid.
    """
    errors = []
    config = {}
    
    # Validate SUPABASE_URL
    supabase_url = os.getenv(ENV_SUPABASE_URL)
    if not supabase_url:
        errors.append(f"{ENV_SUPABASE_URL} is not set")
    elif not validate_url(supabase_url):
        errors.append(f"{ENV_SUPABASE_URL} is not a valid URL: {supabase_url}")
    else:
        config[ENV_SUPABASE_URL] = supabase_url
    
    # Validate SUPABASE_SERVICE_KEY
    service_key = os.getenv(ENV_SUPABASE_SERVICE_KEY)
    if not service_key:
        errors.append(f"{ENV_SUPABASE_SERVICE_KEY} is not set")
    elif not validate_supabase_key(service_key):
        errors.append(f"{ENV_SUPABASE_SERVICE_KEY} appears to be invalid (too short or invalid format)")
    else:
        config[ENV_SUPABASE_SERVICE_KEY] = service_key
    
    # Optional: YOLO_MODEL_PATH (use default if not set)
    model_path = os.getenv(ENV_YOLO_MODEL_PATH, DEFAULT_YOLO_MODEL_PATH)
    config[ENV_YOLO_MODEL_PATH] = model_path
    
    # Optional: TABLE_NAME (use default if not set)
    table_name = os.getenv(ENV_TABLE_NAME, DEFAULT_TABLE_NAME)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        errors.append(f"{ENV_TABLE_NAME} is not a valid table name: {table_name}")
    else:
        config[ENV_TABLE_NAME] = table_name
    
    # Raise error if any validation failed
    if errors:
        error_message = "Environment validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise EnvironmentValidationError(error_message)
    
    return config


def load_and_validate_env() -> Dict[str, str]:
    """
    Load environment variables from .env file and validate them.
    
    This is a convenience function that combines loading from .env file
    with validation.
    
    Returns:
        Dictionary containing validated environment variables.
        
    Raises:
        EnvironmentValidationError: If any required environment variable is
            missing or invalid.
    """
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Validate and return configuration
    return validate_environment()


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value from environment variables.
    
    Args:
        key: The environment variable key.
        default: Default value if the key is not found.
        
    Returns:
        The configuration value or default if not found.
    """
    return os.getenv(key, default)
