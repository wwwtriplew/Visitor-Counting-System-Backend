import os
from datetime import datetime

from dotenv import load_dotenv

from utils.image_utils import base64_to_image
from utils.yolo_utils import load_yolo_model, count_people
from utils.supabase_utils import create_supabase_client, insert_visitor_count


# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def process_image(
    base64_image: str,
    room_id: str,
    model=None,
    supabase_client=None,
    timestamp: datetime = None
) -> dict:
    """
    Process a Base64 image to count people and store the result in Supabase.

    Args:
        base64_image: Base64-encoded image string.
        room_id: Identifier for the room.
        model: Pre-loaded YOLO model (optional, will load if not provided).
        supabase_client: Supabase client (optional, will create if not provided).
        timestamp: Timestamp for the record (optional, defaults to current time).

    Returns:
        Dictionary containing room_id, timestamp, and people_count.
    """
    # Use current timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()

    # Load YOLO model if not provided
    if model is None:
        model = load_yolo_model()

    # Create Supabase client if not provided
    if supabase_client is None:
        supabase_client = create_supabase_client(
            SUPABASE_URL,
            SUPABASE_SERVICE_ROLE_KEY
        )

    # Convert Base64 to image
    image = base64_to_image(base64_image)

    # Count people using YOLO
    people_count = count_people(model, image)

    # Insert record into Supabase
    insert_visitor_count(
        supabase_client,
        room_id,
        timestamp,
        people_count
    )

    return {
        "room_id": room_id,
        "timestamp": timestamp.isoformat(),
        "people_count": people_count
    }


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python process_images.py <base64_image> <room_id>")
        sys.exit(1)

    base64_image = sys.argv[1]
    room_id = sys.argv[2]

    result = process_image(base64_image, room_id)
    print(f"Processed image for room {result['room_id']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"People count: {result['people_count']}")
