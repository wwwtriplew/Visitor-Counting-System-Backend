"""
HTTP Ingestion Server for Visitor Counting System.

This Flask application receives images from cameras via HTTP POST,
processes them through the YOLO pipeline, and stores results in Supabase.

Endpoints:
    POST /api/v1/process-image - Accept JSON with base64 image
    POST /api/v1/process-image-bytes - Accept multipart form with raw JPEG
    GET /health - Health check endpoint
"""

import base64
import logging
import re
import secrets
import time
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env
from server.config import (
    INGESTION_API_KEY,
    MAX_IMAGE_BYTES,
    MAX_CONTENT_LENGTH,
    ROOM_ID_PATTERN,
    SUPABASE_URL_STR,
    SUPABASE_SERVICE_KEY_STR,
    TABLE_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize the processing pipeline (reuse model and Supabase client)
logger.info("Initializing Image Processing Pipeline...")
try:
    pipeline = ImageProcessingPipeline(
        supabase_url=SUPABASE_URL_STR,
        supabase_service_key=SUPABASE_SERVICE_KEY_STR,
        table_name=TABLE_NAME
    )
    logger.info("Pipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize pipeline: {e}")
    raise


# Authentication decorator
def require_api_key(f):
    """Decorator to require X-API-KEY header authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            return jsonify({
                "error": "Missing API key",
                "message": "X-API-KEY header is required"
            }), 401
        
        # Use timing-safe comparison to prevent timing attacks
        # INGESTION_API_KEY is guaranteed to be str (validated at module load)
        assert INGESTION_API_KEY is not None
        if not secrets.compare_digest(api_key, INGESTION_API_KEY):
            logger.warning(f"Invalid API key from {request.remote_addr}")
            return jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is not valid"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_room_id(room_id):
    """Validate room_id format."""
    if not room_id:
        return False, "room_id is required"
    
    if not isinstance(room_id, str):
        return False, "room_id must be a string"
    
    if not re.match(ROOM_ID_PATTERN, room_id):
        return False, f"room_id must match pattern: {ROOM_ID_PATTERN}"
    
    return True, None


def validate_base64_image(base64_string):
    """Validate and decode base64 image string."""
    if not base64_string:
        return False, "", "image is required"
    
    if not isinstance(base64_string, str):
        return False, "", "image must be a string"
    
    # Remove whitespace
    base64_string = base64_string.strip().replace('\n', '').replace('\r', '')
    
    # Try to decode
    try:
        image_bytes = base64.b64decode(base64_string, validate=True)
    except Exception as e:
        return False, "", f"Invalid base64 encoding: {str(e)}"
    
    # Check size
    if len(image_bytes) > MAX_IMAGE_BYTES:
        size_mb = len(image_bytes) / 1024 / 1024
        max_mb = MAX_IMAGE_BYTES / 1024 / 1024
        return False, "", f"Image too large: {size_mb:.2f}MB (max: {max_mb}MB)"
    
    return True, base64_string, None


def parse_timestamp(timestamp_str):
    """Parse optional timestamp string to datetime object."""
    if not timestamp_str:
        return datetime.utcnow()
    
    try:
        # Try ISO format
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except Exception:
        # Fall back to current time
        logger.warning(f"Invalid timestamp format: {timestamp_str}, using current time")
        return datetime.utcnow()


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        200: Service is healthy and ready
    """
    return jsonify({
        "status": "ready",
        "service": "visitor-counting-ingestion-server",
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/api/v1/process-image', methods=['POST'])
@require_api_key
def process_image_json():
    """
    Process image from JSON payload with base64-encoded image.
    
    Expected JSON:
        {
            "image": "<base64_string>",
            "room_id": "room-101",
            "timestamp": "2025-11-26T10:00:00Z"  // optional
        }
    
    Returns:
        200: Successfully processed
        400: Bad request (validation failed)
        413: Payload too large
        500: Processing error
    """
    start_time = time.time()
    
    try:
        # Parse JSON
        if not request.is_json:
            return jsonify({
                "error": "Invalid content type",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        # Validate room_id
        room_id = data.get('room_id')
        valid, error_msg = validate_room_id(room_id)
        if not valid:
            return jsonify({
                "error": "Invalid room_id",
                "message": error_msg
            }), 400
        
        # Validate and decode image
        base64_image = data.get('image')
        valid, validated_image, error_msg = validate_base64_image(base64_image)
        if not valid:
            return jsonify({
                "error": "Invalid image",
                "message": error_msg
            }), 400
        
        # Parse timestamp
        timestamp = parse_timestamp(data.get('timestamp'))
        
        logger.info(f"Processing image for room '{room_id}' from {request.remote_addr}")
        
        # Process through pipeline
        result = pipeline.process_image(
            base64_image=validated_image,
            room_id=room_id,
            timestamp=timestamp
        )
        
        processing_ms = int((time.time() - start_time) * 1000)
        
        if result["success"]:
            logger.info(
                f"Successfully processed room '{room_id}': "
                f"{result['people_count']} people, {processing_ms}ms"
            )
            
            return jsonify({
                "status": "ok",
                "room_id": result["room_id"],
                "people_count": result["people_count"],
                "processing_ms": processing_ms,
                "timestamp": result["timestamp"]
            }), 200
        else:
            logger.error(f"Processing failed for room '{room_id}': {result.get('error')}")
            return jsonify({
                "error": "Processing failed",
                "message": result.get("error", "Unknown error"),
                "room_id": room_id
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/api/v1/process-image-bytes', methods=['POST'])
@require_api_key
def process_image_multipart():
    """
    Process image from multipart form data with raw JPEG file.
    
    Expected form fields:
        - file: raw JPEG image file
        - room_id: string
        - timestamp: optional ISO8601 string
    
    Returns:
        200: Successfully processed
        400: Bad request (validation failed)
        413: Payload too large
        500: Processing error
    """
    start_time = time.time()
    
    try:
        # Validate room_id from form
        room_id = request.form.get('room_id')
        valid, error_msg = validate_room_id(room_id)
        if not valid:
            return jsonify({
                "error": "Invalid room_id",
                "message": error_msg
            }), 400
        
        # Type assertion: room_id is validated and not None at this point
        assert room_id is not None and isinstance(room_id, str)
        
        # Get image file
        if 'file' not in request.files:
            return jsonify({
                "error": "Missing file",
                "message": "The 'file' field is required in multipart form"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "error": "Empty filename",
                "message": "No file was uploaded"
            }), 400
        
        # Read image bytes
        image_bytes = file.read()
        
        # Check size
        if len(image_bytes) > MAX_IMAGE_BYTES:
            size_mb = len(image_bytes) / 1024 / 1024
            max_mb = MAX_IMAGE_BYTES / 1024 / 1024
            return jsonify({
                "error": "Image too large",
                "message": f"Image size {size_mb:.2f}MB exceeds maximum {max_mb}MB"
            }), 413
        
        # Convert to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Parse timestamp
        timestamp = parse_timestamp(request.form.get('timestamp'))
        
        logger.info(f"Processing image file for room '{room_id}' from {request.remote_addr}")
        
        # Process through pipeline
        result = pipeline.process_image(
            base64_image=base64_image,
            room_id=room_id,
            timestamp=timestamp
        )
        
        processing_ms = int((time.time() - start_time) * 1000)
        
        if result["success"]:
            logger.info(
                f"Successfully processed room '{room_id}': "
                f"{result['people_count']} people, {processing_ms}ms"
            )
            
            return jsonify({
                "status": "ok",
                "room_id": result["room_id"],
                "people_count": result["people_count"],
                "processing_ms": processing_ms,
                "timestamp": result["timestamp"]
            }), 200
        else:
            logger.error(f"Processing failed for room '{room_id}': {result.get('error')}")
            return jsonify({
                "error": "Processing failed",
                "message": result.get("error", "Unknown error"),
                "room_id": room_id
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(e):
    """Handle requests that exceed MAX_CONTENT_LENGTH."""
    return jsonify({
        "error": "Payload too large",
        "message": f"Request size exceeds maximum allowed size"
    }), 413


@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(e):
    """Handle 405 errors."""
    return jsonify({
        "error": "Method not allowed",
        "message": f"The {request.method} method is not allowed for this endpoint"
    }), 405


if __name__ == '__main__':
    # This is for development only
    # In production, use gunicorn or another WSGI server
    logger.info(f"Starting development server...")
    logger.warning("WARNING: This is a development server. Use gunicorn for production!")
    app.run(host='0.0.0.0', port=8000, debug=False)
