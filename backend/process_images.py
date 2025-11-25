"""
Main processing script for the Visitor Counting System Backend.

This script orchestrates the entire image processing pipeline:
1. Validates environment variables
2. Converts Base64 images to OpenCV format
3. Runs YOLO inference to count people
4. Stores results in Supabase with retry logic

The script is designed to be production-ready with comprehensive error
handling, logging, and validation at each stage.
"""

import logging
import sys
from datetime import datetime
from typing import Dict, Optional, Any

from backend.config import (
    ENV_SUPABASE_URL,
    ENV_SUPABASE_SERVICE_KEY,
    ENV_YOLO_MODEL_PATH,
    ENV_TABLE_NAME,
    DEFAULT_TABLE_NAME
)
from backend.utils.env_utils import (
    load_and_validate_env,
    EnvironmentValidationError
)
from backend.utils.image_utils import (
    base64_to_image,
    ImageProcessingError
)
from backend.utils.yolo_utils import (
    load_yolo_model,
    count_people,
    YOLOInferenceError
)
from backend.utils.supabase_utils import (
    create_supabase_client,
    insert_visitor_count,
    SupabaseError,
    SupabaseConnectionError,
    SupabaseValidationError
)


# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ImageProcessingPipeline:
    """
    Main pipeline for processing images and counting visitors.
    
    This class encapsulates the entire processing workflow, managing
    resources like the YOLO model and Supabase client for efficient reuse.
    """
    
    def __init__(
        self,
        supabase_url: str,
        supabase_service_key: str,
        model_path: Optional[str] = None,
        table_name: Optional[str] = None
    ):
        """
        Initialize the image processing pipeline.
        
        Args:
            supabase_url: Supabase project URL.
            supabase_service_key: Supabase service role key.
            model_path: Path to YOLO model weights. If None, uses default.
            table_name: Supabase table name. If None, uses default.
            
        Raises:
            SupabaseConnectionError: If Supabase client creation fails.
            YOLOInferenceError: If YOLO model loading fails.
        """
        self.table_name = table_name or DEFAULT_TABLE_NAME
        
        logger.info("Initializing Image Processing Pipeline...")
        
        # Initialize Supabase client
        try:
            self.supabase_client = create_supabase_client(
                supabase_url,
                supabase_service_key
            )
            logger.info("Supabase client initialized")
        except SupabaseConnectionError as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
        
        # Load YOLO model
        try:
            self.model = load_yolo_model(model_path)
            logger.info("YOLO model loaded")
        except YOLOInferenceError as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            raise
        
        logger.info("Pipeline initialization complete")
    
    def process_image(
        self,
        base64_image: str,
        room_id: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Process a single Base64-encoded image through the entire pipeline.
        
        This method:
        1. Converts Base64 to OpenCV image
        2. Runs YOLO inference to count people
        3. Inserts the result into Supabase
        4. Returns processing results
        
        Args:
            base64_image: Base64-encoded image string (with or without data URL prefix).
            room_id: Identifier for the room being monitored.
            timestamp: Timestamp for the count. If None, uses current time.
        
        Returns:
            Dictionary containing:
                - room_id: The room identifier
                - timestamp: ISO format timestamp
                - people_count: Number of people detected
                - success: True if processing succeeded
                - error: Error message if processing failed (only present on failure)
        """
        # Use current timestamp if not provided
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            logger.info(f"Processing image for room '{room_id}' at {timestamp.isoformat()}")
            
            # Step 1: Convert Base64 to image
            logger.debug("Converting Base64 to image...")
            try:
                image = base64_to_image(base64_image)
            except ImageProcessingError as e:
                error_msg = f"Image conversion failed: {str(e)}"
                logger.error(error_msg)
                return {
                    "room_id": room_id,
                    "timestamp": timestamp.isoformat(),
                    "people_count": None,
                    "success": False,
                    "error": error_msg
                }
            
            # Step 2: Count people using YOLO
            logger.debug("Running YOLO inference...")
            try:
                people_count = count_people(self.model, image)
            except YOLOInferenceError as e:
                error_msg = f"YOLO inference failed: {str(e)}"
                logger.error(error_msg)
                return {
                    "room_id": room_id,
                    "timestamp": timestamp.isoformat(),
                    "people_count": None,
                    "success": False,
                    "error": error_msg
                }
            
            # Step 3: Insert into Supabase
            logger.debug(f"Inserting count ({people_count}) into Supabase...")
            try:
                insert_visitor_count(
                    self.supabase_client,
                    room_id,
                    timestamp,
                    people_count,
                    table_name=self.table_name
                )
            except (SupabaseValidationError, SupabaseError) as e:
                error_msg = f"Supabase insertion failed: {str(e)}"
                logger.error(error_msg)
                return {
                    "room_id": room_id,
                    "timestamp": timestamp.isoformat(),
                    "people_count": people_count,
                    "success": False,
                    "error": error_msg
                }
            
            # Success!
            logger.info(
                f"Successfully processed image for room '{room_id}': "
                f"{people_count} people detected"
            )
            
            return {
                "room_id": room_id,
                "timestamp": timestamp.isoformat(),
                "people_count": people_count,
                "success": True
            }
            
        except Exception as e:
            # Catch any unexpected errors
            error_msg = f"Unexpected error during processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "room_id": room_id,
                "timestamp": timestamp.isoformat(),
                "people_count": None,
                "success": False,
                "error": error_msg
            }


def process_image(
    base64_image: str,
    room_id: str,
    model=None,
    supabase_client=None,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Process a Base64 image to count people and store the result in Supabase.
    
    This is a convenience function that maintains backward compatibility.
    For production use, consider using the ImageProcessingPipeline class
    for better resource management.

    Args:
        base64_image: Base64-encoded image string.
        room_id: Identifier for the room.
        model: Pre-loaded YOLO model (optional, will load if not provided).
        supabase_client: Supabase client (optional, will create if not provided).
        timestamp: Timestamp for the record (optional, defaults to current time).

    Returns:
        Dictionary containing processing results (room_id, timestamp, people_count, success).
        
    Raises:
        EnvironmentValidationError: If environment variables are invalid.
        Various processing errors if allow_failure is False.
    """
    # Use current timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    try:
        # Load environment configuration if clients not provided
        if model is None or supabase_client is None:
            try:
                config = load_and_validate_env()
            except EnvironmentValidationError as e:
                logger.error(f"Environment validation failed: {str(e)}")
                raise
        
        # Load YOLO model if not provided
        if model is None:
            model_path = config.get(ENV_YOLO_MODEL_PATH)
            model = load_yolo_model(model_path)
        
        # Create Supabase client if not provided
        if supabase_client is None:
            supabase_url = config[ENV_SUPABASE_URL]
            service_key = config[ENV_SUPABASE_SERVICE_KEY]
            supabase_client = create_supabase_client(supabase_url, service_key)
        
        # Get table name from config
        table_name = config.get(ENV_TABLE_NAME, DEFAULT_TABLE_NAME) \
            if 'config' in locals() else DEFAULT_TABLE_NAME
        
        # Convert Base64 to image
        image = base64_to_image(base64_image)
        
        # Count people using YOLO
        people_count = count_people(model, image)
        
        # Insert record into Supabase
        insert_visitor_count(
            supabase_client,
            room_id,
            timestamp,
            people_count,
            table_name=table_name
        )
        
        return {
            "room_id": room_id,
            "timestamp": timestamp.isoformat(),
            "people_count": people_count,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return {
            "room_id": room_id,
            "timestamp": timestamp.isoformat(),
            "people_count": None,
            "success": False,
            "error": str(e)
        }


def main():
    """
    Main entry point for command-line usage.
    
    Usage:
        python process_images.py <base64_image> <room_id> [timestamp]
        
    Examples:
        python process_images.py "$(base64 -i image.jpg)" room_101
        python process_images.py "<base64-string>" lobby "2025-11-25T14:30:00"
    """
    # Parse command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python process_images.py <base64_image> <room_id> [timestamp]")
        print("\nArguments:")
        print("  base64_image: Base64-encoded image string")
        print("  room_id: Identifier for the room (e.g., 'room_101', 'lobby')")
        print("  timestamp: Optional ISO format timestamp (defaults to current time)")
        sys.exit(1)
    
    base64_image = sys.argv[1]
    room_id = sys.argv[2]
    timestamp = None
    
    # Parse optional timestamp
    if len(sys.argv) >= 4:
        try:
            timestamp = datetime.fromisoformat(sys.argv[3])
        except ValueError as e:
            logger.error(f"Invalid timestamp format: {sys.argv[3]}")
            print(f"Error: Invalid timestamp format. Use ISO format (e.g., '2025-11-25T14:30:00')")
            sys.exit(1)
    
    try:
        # Validate environment variables
        logger.info("Validating environment configuration...")
        config = load_and_validate_env()
        
        # Initialize the processing pipeline
        pipeline = ImageProcessingPipeline(
            supabase_url=config[ENV_SUPABASE_URL],
            supabase_service_key=config[ENV_SUPABASE_SERVICE_KEY],
            model_path=config.get(ENV_YOLO_MODEL_PATH),
            table_name=config.get(ENV_TABLE_NAME)
        )
        
        # Process the image
        result = pipeline.process_image(base64_image, room_id, timestamp)
        
        # Print results
        if result["success"]:
            print(f"\n✓ Successfully processed image for room '{result['room_id']}'")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  People count: {result['people_count']}")
            sys.exit(0)
        else:
            print(f"\n✗ Failed to process image for room '{result['room_id']}'")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except EnvironmentValidationError as e:
        logger.error(f"Environment validation failed: {str(e)}")
        print(f"\n✗ Environment validation failed:")
        print(f"  {str(e)}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\n\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
