"""
YOLO inference utilities for the Visitor Counting System Backend.

This module provides functions for loading YOLO models and performing
person detection with optimized inference and validation. It includes
detailed logging and error handling to ensure reliable detection results.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from ultralytics import YOLO

from backend.config import (
    PERSON_CLASS_ID,
    YOLO_CONFIDENCE_THRESHOLD,
    MIN_PEOPLE_COUNT,
    MAX_PEOPLE_COUNT,
    DEFAULT_YOLO_MODEL_PATH
)


# Configure logging
logger = logging.getLogger(__name__)


class YOLOInferenceError(Exception):
    """Raised when YOLO inference operations fail."""
    pass


def load_yolo_model(model_path: Optional[str] = None) -> YOLO:
    """
    Load a YOLO v8 model for person detection.
    
    This function loads the YOLO model and validates that it's ready for
    inference. The model is cached by Ultralytics for efficient reuse.

    Args:
        model_path: Path to the YOLO model weights file. If None, uses the
            default model path from config. Can be a local file path or
            a model name that will be downloaded from Ultralytics.

    Returns:
        Loaded and validated YOLO model ready for inference.
        
    Raises:
        YOLOInferenceError: If the model fails to load or is invalid.
    """
    if model_path is None:
        model_path = DEFAULT_YOLO_MODEL_PATH
    
    try:
        logger.info(f"Loading YOLO model from: {model_path}")
        
        # Load the YOLO model
        model = YOLO(model_path)
        
        # Validate the model loaded successfully
        if model is None:
            raise YOLOInferenceError("Failed to load YOLO model - model is None")
        
        # Log model information
        model_info = f"YOLO model loaded successfully"
        if hasattr(model, 'names') and model.names:
            # Check if 'person' class is available
            if PERSON_CLASS_ID in model.names:
                model_info += f" (person class: '{model.names[PERSON_CLASS_ID]}')"
            else:
                logger.warning(
                    f"PERSON_CLASS_ID ({PERSON_CLASS_ID}) not found in model classes. "
                    f"Available classes: {list(model.names.values())}"
                )
        
        logger.info(model_info)
        
        return model
        
    except YOLOInferenceError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Catch any unexpected errors during model loading
        logger.error(f"Failed to load YOLO model: {str(e)}")
        raise YOLOInferenceError(f"Failed to load YOLO model from '{model_path}': {str(e)}")


def validate_detection_results(people_count: int) -> None:
    """
    Validate that detection results are within reasonable bounds.
    
    Args:
        people_count: The detected number of people.
        
    Raises:
        YOLOInferenceError: If the count is outside valid bounds.
    """
    if not isinstance(people_count, int):
        raise YOLOInferenceError(f"People count must be an integer, got {type(people_count)}")
    
    if people_count < MIN_PEOPLE_COUNT:
        raise YOLOInferenceError(
            f"People count ({people_count}) is below minimum ({MIN_PEOPLE_COUNT})"
        )
    
    if people_count > MAX_PEOPLE_COUNT:
        logger.warning(
            f"People count ({people_count}) exceeds maximum expected value ({MAX_PEOPLE_COUNT}). "
            f"This may indicate a detection error."
        )


def count_people(
    model: YOLO, 
    image: np.ndarray, 
    confidence: Optional[float] = None
) -> int:
    """
    Count the number of people in an image using YOLO object detection.
    
    This function runs YOLO inference on the provided image and counts
    detections of the 'person' class that meet the confidence threshold.
    It includes validation and detailed logging for debugging.

    Args:
        model: Loaded YOLO model instance.
        image: OpenCV image as numpy array (BGR format).
        confidence: Minimum confidence threshold for detections (0.0-1.0).
            If None, uses the default from config.

    Returns:
        Number of people detected in the image (validated count).
        
    Raises:
        YOLOInferenceError: If inference fails or results are invalid.
    """
    try:
        # Use default confidence if not specified
        if confidence is None:
            confidence = YOLO_CONFIDENCE_THRESHOLD
        
        # Validate confidence threshold
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            raise YOLOInferenceError(
                f"Invalid confidence threshold: {confidence}. Must be between 0 and 1"
            )
        
        # Validate image
        if image is None or not isinstance(image, np.ndarray):
            raise YOLOInferenceError("Invalid image provided for inference")
        
        if image.size == 0:
            raise YOLOInferenceError("Image has zero size")
        
        logger.debug(
            f"Running YOLO inference on image with shape {image.shape}, "
            f"confidence threshold: {confidence}"
        )
        
        # Run YOLO inference
        # verbose=False suppresses per-image output from Ultralytics
        results = model(image, verbose=False)
        
        if not results:
            logger.warning("YOLO inference returned no results")
            return 0
        
        # Count people in the detections
        people_count = 0
        detections_info = []
        
        for result in results:
            # Check if this result has any detections
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
            
            # Iterate through detected objects
            for box in boxes:
                # Extract class ID and confidence score
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Count if this is a person with sufficient confidence
                if class_id == PERSON_CLASS_ID and conf >= confidence:
                    people_count += 1
                    
                    # Store detection info for logging (optional, for debugging)
                    if logger.isEnabledFor(logging.DEBUG):
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        detections_info.append({
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2]
                        })
        
        # Log detection results
        if detections_info:
            logger.debug(
                f"Detected {people_count} people. "
                f"Confidences: {[d['confidence'] for d in detections_info]}"
            )
        else:
            logger.debug(f"Detected {people_count} people")
        
        # Validate the count is reasonable
        validate_detection_results(people_count)
        
        return people_count
        
    except YOLOInferenceError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Catch any unexpected errors during inference
        logger.error(f"Unexpected error during YOLO inference: {str(e)}")
        raise YOLOInferenceError(f"YOLO inference failed: {str(e)}")


def get_people_detections_with_boxes(
    model: YOLO,
    image: np.ndarray,
    confidence: Optional[float] = None
) -> List[Tuple[float, List[float]]]:
    """
    Get detailed detection information including bounding boxes.
    
    This function is useful for advanced use cases where you need more than
    just the count, such as tracking specific individuals or analyzing
    spatial distribution.
    
    Args:
        model: Loaded YOLO model instance.
        image: OpenCV image as numpy array (BGR format).
        confidence: Minimum confidence threshold for detections (0.0-1.0).
            If None, uses the default from config.
    
    Returns:
        List of tuples containing (confidence_score, [x1, y1, x2, y2])
        for each detected person.
        
    Raises:
        YOLOInferenceError: If inference fails or results are invalid.
    """
    try:
        # Use default confidence if not specified
        if confidence is None:
            confidence = YOLO_CONFIDENCE_THRESHOLD
        
        # Validate inputs
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            raise YOLOInferenceError(
                f"Invalid confidence threshold: {confidence}. Must be between 0 and 1"
            )
        
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise YOLOInferenceError("Invalid image provided for inference")
        
        # Run YOLO inference
        results = model(image, verbose=False)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
            
            for box in boxes:
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                if class_id == PERSON_CLASS_ID and conf >= confidence:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append((conf, [x1, y1, x2, y2]))
        
        logger.debug(f"Retrieved {len(detections)} person detections with bounding boxes")
        
        return detections
        
    except YOLOInferenceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting detection boxes: {str(e)}")
        raise YOLOInferenceError(f"Failed to get detection boxes: {str(e)}")
