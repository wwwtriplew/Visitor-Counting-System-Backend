import numpy as np
from ultralytics import YOLO


# COCO class ID for "person" is 0
PERSON_CLASS_ID = 0


def load_yolo_model(model_path: str = "yolov8n.pt") -> YOLO:
    """
    Load a YOLO v8 model.

    Args:
        model_path: Path to the YOLO model weights file.

    Returns:
        Loaded YOLO model.
    """
    model = YOLO(model_path)
    return model


def count_people(model: YOLO, image: np.ndarray, confidence: float = 0.5) -> int:
    """
    Count the number of people in an image using YOLO.

    Args:
        model: Loaded YOLO model.
        image: OpenCV image as numpy array.
        confidence: Minimum confidence threshold for detections.

    Returns:
        Number of people detected in the image.
    """
    results = model(image, verbose=False)

    people_count = 0
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        for box in boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])

            if class_id == PERSON_CLASS_ID and conf >= confidence:
                people_count += 1

    return people_count
