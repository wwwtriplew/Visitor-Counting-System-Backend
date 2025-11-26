"""
Configuration for the HTTP Ingestion Server.

This module loads environment variables and defines constants
for the ingestion server that receives images from cameras.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# API Security
INGESTION_API_KEY = os.getenv("INGESTION_API_KEY")
if not INGESTION_API_KEY:
    raise ValueError("INGESTION_API_KEY environment variable must be set")

# Image Processing Limits
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB (allow overhead)

# Validation Patterns
ROOM_ID_PATTERN = r'^[A-Za-z0-9_-]{1,64}$'

# Supabase Configuration (inherited from main app)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = os.getenv("TABLE_NAME", "detections")

# Validate required environment variables
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable must be set")
if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable must be set")

# Type-safe constants (validated above, so we know they're not None)
SUPABASE_URL_STR: str = SUPABASE_URL
SUPABASE_SERVICE_KEY_STR: str = SUPABASE_SERVICE_KEY
