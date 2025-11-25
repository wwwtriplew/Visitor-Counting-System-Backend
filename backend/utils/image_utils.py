import base64
import cv2
import numpy as np


def base64_to_image(base64_string: str) -> np.ndarray:
    """
    Convert a Base64-encoded string to an OpenCV image (numpy array).

    Args:
        base64_string: Base64-encoded image string.

    Returns:
        OpenCV image as numpy array.
    """
    # Remove data URL prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    image_bytes = base64.b64decode(base64_string)
    np_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    return image


def image_to_jpeg_bytes(image: np.ndarray, quality: int = 95) -> bytes:
    """
    Convert an OpenCV image to JPEG bytes.

    Args:
        image: OpenCV image as numpy array.
        quality: JPEG quality (0-100).

    Returns:
        JPEG image as bytes.
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, jpeg_bytes = cv2.imencode(".jpg", image, encode_param)

    return jpeg_bytes.tobytes()
