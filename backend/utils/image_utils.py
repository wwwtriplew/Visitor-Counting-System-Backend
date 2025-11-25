"""
Image processing utilities for the Visitor Counting System Backend.

This module provides functions for converting between different image formats,
with robust error handling and validation to ensure image data is processed
correctly before YOLO inference.
"""

import base64
import logging
from typing import Optional

import cv2
import numpy as np

from backend.config import JPEG_QUALITY, MAX_IMAGE_SIZE


# Configure logging
logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Raised when image processing operations fail."""
    pass


def validate_base64_string(base64_string: str) -> None:
    """
    Validate that a string is a properly formatted Base64-encoded image.
    
    Args:
        base64_string: The Base64 string to validate.
        
    Raises:
        ImageProcessingError: If the string is invalid or too large.
    """
    if not base64_string or not isinstance(base64_string, str):
        raise ImageProcessingError("Base64 string is empty or not a string")
    
    # Remove data URL prefix if present for size calculation
    clean_string = base64_string.split(",")[1] if "," in base64_string else base64_string
    
    # Check if the string is too large (approximate size check)
    estimated_size = len(clean_string) * 3 / 4  # Base64 overhead
    if estimated_size > MAX_IMAGE_SIZE:
        raise ImageProcessingError(
            f"Image size ({estimated_size / 1024 / 1024:.2f} MB) exceeds "
            f"maximum allowed size ({MAX_IMAGE_SIZE / 1024 / 1024:.2f} MB)"
        )
    
    # Validate Base64 format (basic check for valid characters)
    if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' 
               for c in clean_string):
        raise ImageProcessingError("Invalid Base64 string format")


def base64_to_image(base64_string: str) -> np.ndarray:
    """
    Convert a Base64-encoded string to an OpenCV image (numpy array).
    
    This function decodes a Base64 string into a color image that can be
    processed by YOLO. It includes validation and error handling to ensure
    the conversion succeeds and produces a valid image.

    Args:
        base64_string: Base64-encoded image string. Can include data URL prefix
            (e.g., "data:image/jpeg;base64,/9j/4AAQ...").

    Returns:
        OpenCV image as numpy array in BGR color format.
        
    Raises:
        ImageProcessingError: If the Base64 string is invalid, decoding fails,
            or the result is not a valid image.
    """
    try:
        # Validate the input string
        validate_base64_string(base64_string)
        
        # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        # Decode Base64 string to bytes
        try:
            image_bytes = base64.b64decode(base64_string, validate=True)
        except Exception as e:
            raise ImageProcessingError(f"Failed to decode Base64 string: {str(e)}")
        
        # Convert bytes to numpy array
        np_array = np.frombuffer(image_bytes, dtype=np.uint8)
        
        if len(np_array) == 0:
            raise ImageProcessingError("Decoded image data is empty")
        
        # Decode image using OpenCV
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        # Validate the decoded image
        if image is None:
            raise ImageProcessingError(
                "Failed to decode image - the data may be corrupted or in an unsupported format"
            )
        
        if image.size == 0:
            raise ImageProcessingError("Decoded image has zero size")
        
        # Log successful conversion
        logger.debug(f"Successfully decoded image with shape: {image.shape}")
        
        return image
        
    except ImageProcessingError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in base64_to_image: {str(e)}")
        raise ImageProcessingError(f"Unexpected error during image conversion: {str(e)}")


def validate_image(image: np.ndarray) -> None:
    """
    Validate that an image array is suitable for processing.
    
    Args:
        image: OpenCV image as numpy array.
        
    Raises:
        ImageProcessingError: If the image is invalid.
    """
    if image is None:
        raise ImageProcessingError("Image is None")
    
    if not isinstance(image, np.ndarray):
        raise ImageProcessingError("Image is not a numpy array")
    
    if image.size == 0:
        raise ImageProcessingError("Image has zero size")
    
    if len(image.shape) < 2:
        raise ImageProcessingError("Image must be at least 2-dimensional")
    
    # Check for reasonable image dimensions (not too small, not too large)
    height, width = image.shape[:2]
    if height < 10 or width < 10:
        raise ImageProcessingError(f"Image dimensions too small: {width}x{height}")
    
    if height > 10000 or width > 10000:
        raise ImageProcessingError(f"Image dimensions too large: {width}x{height}")


def image_to_jpeg_bytes(
    image: np.ndarray, 
    quality: Optional[int] = None
) -> bytes:
    """
    Convert an OpenCV image to JPEG bytes with compression.
    
    This function is useful for storing or transmitting processed images
    in a compressed format.

    Args:
        image: OpenCV image as numpy array.
        quality: JPEG quality (0-100). Higher values mean better quality
            but larger file sizes. If None, uses the default from config.

    Returns:
        JPEG image as bytes.
        
    Raises:
        ImageProcessingError: If the image is invalid or encoding fails.
    """
    try:
        # Validate the input image
        validate_image(image)
        
        # Use default quality if not specified
        if quality is None:
            quality = JPEG_QUALITY
        
        # Validate quality parameter
        if not isinstance(quality, int) or quality < 0 or quality > 100:
            raise ImageProcessingError(f"Invalid JPEG quality: {quality}. Must be 0-100")
        
        # Encode image to JPEG format
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, jpeg_encoded = cv2.imencode(".jpg", image, encode_param)
        
        if not success:
            raise ImageProcessingError("Failed to encode image to JPEG format")
        
        jpeg_bytes = jpeg_encoded.tobytes()
        
        # Log successful conversion
        logger.debug(f"Successfully encoded image to JPEG ({len(jpeg_bytes)} bytes)")
        
        return jpeg_bytes
        
    except ImageProcessingError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in image_to_jpeg_bytes: {str(e)}")
        raise ImageProcessingError(f"Unexpected error during JPEG encoding: {str(e)}")
