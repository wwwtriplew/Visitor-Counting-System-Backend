# Visitor-Counting-System-Backend

A backend implementation for an internal activity to monitor visitor distribution across rooms in a building using YOLO v8 for people detection.

## Features

- Accept Base64-encoded images
- Convert images to JPEG format
- Run YOLO v8 inference to count people
- Store visitor counts (room_id, timestamp, people_count) in Supabase

## Project Structure

```
backend/
  process_images.py       # Main processing script
  utils/
    image_utils.py        # Image conversion utilities
    yolo_utils.py         # YOLO inference utilities
    supabase_utils.py     # Supabase database utilities
.env.example              # Environment variables template
requirements.txt          # Python dependencies
README.md                 # This file
.gitignore                # Git ignore rules
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wwwtriplew/Visitor-Counting-System-Backend.git
cd Visitor-Counting-System-Backend
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

5. Update the `.env` file with your Supabase credentials:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Supabase Setup

Create a table in your Supabase project with the following structure:

```sql
CREATE TABLE visitor_counts (
    id SERIAL PRIMARY KEY,
    room_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    people_count INTEGER NOT NULL
);
```

## Usage

### As a module

```python
from backend.process_images import process_image

# Process a Base64-encoded image
result = process_image(
    base64_image="<base64_encoded_image_string>",
    room_id="room-101"
)

print(f"People count: {result['people_count']}")
```

### From command line

```bash
cd backend
python process_images.py "<base64_image>" "<room_id>"
```

## Dependencies

- `supabase` - Supabase Python client
- `ultralytics` - YOLO v8 implementation
- `opencv-python` - Image processing
- `python-dotenv` - Environment variable management
