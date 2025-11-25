# Visitor-Counting-System-Backend

# Overview

This repository contains the backend implementation for an internal activity to monitor visitor distribution across rooms in a building. Cameras installed in each room capture images every minute. A high-performance backend computer processes these images using a YOLO model to count the number of people in each room. The processed data (room ID, timestamp, people count) is stored in Supabase, which acts as the central database.
A separate front-end system (static website hosted on GitHub Pages) fetches this data and displays the latest occupancy status for guards and visitors. This README includes front-end context for clarity, but the code in this repository is backend only.
A backend implementation for an internal activity to monitor visitor distribution across rooms in a building using YOLO v8 for people detection.

# Expected Data Flow

Cameras → Base64 images → Computation Computer → JPEG conversion → YOLO analysis → Supabase → Front-End Computer → Display latest occupancy

# Why Supabase?

Why Supabase?
Supabase provides:

A PostgreSQL database for structured storage.
REST and Realtime APIs for easy data access.
Built-in authentication and Row Level Security (RLS) for secure operations.
Free and simple

# Architecture 

Architecture

Computation Computer (Backend):

Receives Base64 images from cameras.
Converts to JPEG.
Runs YOLO inference to count people.
Sends {room_id, timestamp, people_count} to Supabase using the service role key.


Supabase:

Stores all records in a single table room_stats.
Provides APIs for read/write operations.

# Table Creation SQL

CREATE TABLE room_stats (
  id BIGSERIAL PRIMARY KEY,
  room_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  people_count INT NOT NULL
);

# Environment variables

SUPABASE_URL=<your-supabase-url>
SUPABASE_SERVICE_KEY=<your-service-role-key>


# Front-End Computer:

Static site hosted on GitHub Pages.
Fetches latest snapshot using anon key.
Displays occupancy per room (future: color coding, floor plan UI).

# Tech Stack

Tech Stack

Backend:

Python 3.x
YOLO (Ultralytics or custom model)
Supabase Python SDK


Frontend:

HTML + JavaScript
Supabase JS SDK
GitHub Pages for hosting


Database:

Supabase PostgreSQL

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


## Future plan for front end (not considered in this repo)

Roadmap For Front End repo

Phase 1: Manual refresh on front end, grid layout for rooms.
Phase 2: Real-time updates using Supabase Realtime.
Phase 3: Floor plan overlay for visual clarity.
Phase 4: Color coding for occupancy thresholds.
Phase 5: Data export for analysis (CSV).
Phase 6: Historical trend charts and heatmaps.