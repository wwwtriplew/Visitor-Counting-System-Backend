"""
Configuration module for the Visitor Counting System Backend.

This module defines constants, default values, and configuration parameters
used throughout the application. Centralizing these values makes the system
easier to maintain and configure.
"""

# YOLO Model Configuration
DEFAULT_YOLO_MODEL_PATH = "yolov8n.pt"  # Nano model for faster inference
YOLO_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for person detection
PERSON_CLASS_ID = 0  # COCO dataset class ID for "person"

# Image Processing Configuration
JPEG_QUALITY = 95  # JPEG compression quality (0-100)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # Maximum image size in bytes (10MB)

# Supabase Configuration
DEFAULT_TABLE_NAME = "detections"  # Default table name for visitor counts
MAX_RETRY_ATTEMPTS = 3  # Maximum number of retry attempts for failed operations
RETRY_DELAY_SECONDS = 2  # Delay between retry attempts in seconds
CONNECTION_TIMEOUT = 10  # Supabase connection timeout in seconds

# Validation Configuration
VALID_ROOM_ID_PATTERN = r'^[A-Za-z0-9_-]+$'  # Regex pattern for valid room IDs
MIN_PEOPLE_COUNT = 0  # Minimum valid people count
MAX_PEOPLE_COUNT = 1000  # Maximum reasonable people count per room

# Environment Variable Keys
ENV_SUPABASE_URL = "SUPABASE_URL"
ENV_SUPABASE_SERVICE_KEY = "SUPABASE_SERVICE_KEY"
ENV_YOLO_MODEL_PATH = "YOLO_MODEL_PATH"
ENV_TABLE_NAME = "TABLE_NAME"
