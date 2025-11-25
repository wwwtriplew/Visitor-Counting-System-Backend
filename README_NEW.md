# Visitor-Counting-System-Backend

A production-ready backend system for monitoring visitor distribution across rooms using YOLO v8 object detection and Supabase for data storage. This system processes images from cameras installed in each room, counts people using AI, and stores the results for real-time monitoring.

## Overview

This repository contains the backend implementation for an internal activity to monitor visitor distribution across rooms in a building. Cameras installed in each room capture images every minute. A high-performance backend computer processes these images using a YOLO model to count the number of people in each room. The processed data (room ID, timestamp, people count) is stored in Supabase, which acts as the central database.

A separate front-end system (static website hosted on GitHub Pages) fetches this data and displays the latest occupancy status for guards and visitors.

## Architecture

### System Components

1. **Computation Computer (Backend)**:
   - Receives Base64-encoded images from cameras
   - Converts images to JPEG format
   - Runs YOLO v8 inference to detect and count people
   - Validates detection results
   - Sends `{room_id, timestamp, people_count}` to Supabase using the service role key
   - Implements retry logic for failed operations

2. **Supabase (Database & API)**:
   - Stores all records in the `room_stats` table
   - Provides REST and Realtime APIs for data access
   - Handles authentication and security via Row Level Security (RLS)
   - Offers free tier with generous limits

3. **Front-End Computer** (separate repository):
   - Static site hosted on GitHub Pages
   - Fetches latest snapshot using anon key
   - Displays occupancy per room with visual indicators
   - Future features: color coding, interactive floor plan UI

### Data Flow

```
Cameras → Base64 Images → Backend Computer → JPEG Conversion → 
YOLO Analysis → Validation → Supabase → Front-End → Display
```

## Features

### Core Functionality
- ✅ Accept and validate Base64-encoded images
- ✅ Convert images to OpenCV format with error handling
- ✅ Run YOLO v8 inference with optimized pipeline
- ✅ Count people with configurable confidence threshold
- ✅ Validate detection results (bounds checking)
- ✅ Store visitor counts in Supabase with retry logic
- ✅ Comprehensive error handling and logging
- ✅ Environment variable validation

### Production Features
- ✅ Modular, maintainable code structure
- ✅ Detailed docstrings and inline comments
- ✅ Custom exception classes for error handling
- ✅ Retry logic with exponential backoff
- ✅ Network failure resilience
- ✅ Input validation at every stage
- ✅ Configurable parameters via environment variables
- ✅ Logging for monitoring and debugging

## Tech Stack

### Backend
- **Python 3.8+**: Core programming language
- **YOLO v8 (Ultralytics)**: Object detection for person counting
- **OpenCV**: Image processing and conversion
- **Supabase Python SDK**: Database integration
- **python-dotenv**: Environment variable management

### Database
- **Supabase PostgreSQL**: Structured data storage with real-time capabilities

## Project Structure

```
backend/
├── config.py                 # Configuration constants and defaults
├── process_images.py         # Main processing script and CLI
├── utils/
│   ├── __init__.py
│   ├── env_utils.py          # Environment variable validation
│   ├── image_utils.py        # Image conversion with error handling
│   ├── yolo_utils.py         # YOLO inference and person detection
│   └── supabase_utils.py     # Supabase integration with retry logic
requirements.txt              # Python dependencies
.env.example                  # Environment variables template
README.md                     # This file
```

## Database Schema

### Table: `room_stats`

Stores visitor count records with timestamp information.

```sql
CREATE TABLE room_stats (
  id BIGSERIAL PRIMARY KEY,
  room_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  people_count INT NOT NULL,
  
  -- Optional: Add indexes for better query performance
  CONSTRAINT people_count_non_negative CHECK (people_count >= 0)
);

-- Indexes for efficient queries
CREATE INDEX idx_room_stats_room_id ON room_stats(room_id);
CREATE INDEX idx_room_stats_timestamp ON room_stats(timestamp DESC);
CREATE INDEX idx_room_stats_room_timestamp ON room_stats(room_id, timestamp DESC);
```

### Data Format

Each record contains:
- `id` (BIGSERIAL): Auto-generated unique identifier
- `room_id` (TEXT): Room identifier (e.g., "room_101", "lobby", "conference_a")
  - Must match pattern: `^[A-Za-z0-9_-]+$`
  - Maximum length: 50 characters
- `timestamp` (TIMESTAMPTZ): ISO 8601 timestamp with timezone
  - Example: `2025-11-25T14:30:00+00:00`
- `people_count` (INT): Number of people detected
  - Must be non-negative
  - Maximum: 1000 (configurable in `backend/config.py`)

### Example Records

```json
[
  {
    "id": 1,
    "room_id": "lobby",
    "timestamp": "2025-11-25T09:00:00+00:00",
    "people_count": 12
  },
  {
    "id": 2,
    "room_id": "room_101",
    "timestamp": "2025-11-25T09:01:00+00:00",
    "people_count": 3
  }
]
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Supabase account (free tier available)
- Sufficient disk space for YOLO model (~6MB for nano model)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/wwwtriplew/Visitor-Counting-System-Backend.git
   cd Visitor-Counting-System-Backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Set up Supabase**:
   - Create a new Supabase project at https://supabase.com
   - Run the SQL schema from the "Database Schema" section above
   - Copy your project URL and service role key to `.env`

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required: Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Optional: Model Configuration
YOLO_MODEL_PATH=yolov8n.pt  # Default: yolov8n.pt (nano model)

# Optional: Database Configuration
TABLE_NAME=room_stats  # Default: room_stats
```

### Configuration Parameters

Edit `backend/config.py` to customize:

- `YOLO_CONFIDENCE_THRESHOLD`: Detection confidence (default: 0.5)
- `MAX_IMAGE_SIZE`: Maximum image size in bytes (default: 10MB)
- `MAX_RETRY_ATTEMPTS`: Retry attempts for failed operations (default: 3)
- `RETRY_DELAY_SECONDS`: Initial retry delay (default: 2s)
- `MAX_PEOPLE_COUNT`: Maximum expected people per room (default: 1000)

## Usage

### Command Line Interface

```bash
# Basic usage with current timestamp
python -m backend.process_images "<base64-image>" "room_id"

# With custom timestamp
python -m backend.process_images "<base64-image>" "lobby" "2025-11-25T14:30:00"

# Using a file
python -m backend.process_images "$(base64 -i image.jpg)" "room_101"
```

### Python API

#### Using the Pipeline Class (Recommended)

```python
from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env

# Load and validate configuration
config = load_and_validate_env()

# Initialize pipeline (reuses model and client)
pipeline = ImageProcessingPipeline(
    supabase_url=config["SUPABASE_URL"],
    supabase_service_key=config["SUPABASE_SERVICE_KEY"]
)

# Process multiple images efficiently
for image_data, room in image_queue:
    result = pipeline.process_image(image_data, room)
    
    if result["success"]:
        print(f"✓ Room {result['room_id']}: {result['people_count']} people")
    else:
        print(f"✗ Error: {result['error']}")
```

#### Using the Standalone Function

```python
from backend.process_images import process_image

# Process a single image (loads model and client each time)
result = process_image(
    base64_image="<base64-string>",
    room_id="conference_room_a"
)

print(f"Count: {result['people_count']}, Success: {result['success']}")
```

### Integration Example

```python
import requests
from backend.process_images import ImageProcessingPipeline

# Initialize pipeline once
pipeline = ImageProcessingPipeline(
    supabase_url="https://your-project.supabase.co",
    supabase_service_key="your-key"
)

# Fetch image from camera
response = requests.get("http://camera-ip/snapshot")
base64_image = response.json()["image"]

# Process and store
result = pipeline.process_image(base64_image, "room_205")

if not result["success"]:
    # Handle error (send alert, log, retry, etc.)
    print(f"Processing failed: {result['error']}")
```

## Front-End Integration

### Fetching Latest Data

The front-end should use the Supabase **anon key** (not the service role key) to fetch data:

```javascript
// Initialize Supabase client (front-end)
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseAnonKey = 'your-anon-key'
const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Fetch latest count for all rooms
async function getLatestCounts() {
  const { data, error } = await supabase
    .from('room_stats')
    .select('room_id, timestamp, people_count')
    .order('timestamp', { ascending: false })
    .limit(100)
  
  if (error) console.error('Error:', error)
  return data
}

// Fetch latest count for a specific room
async function getRoomCount(roomId) {
  const { data, error } = await supabase
    .from('room_stats')
    .select('*')
    .eq('room_id', roomId)
    .order('timestamp', { ascending: false })
    .limit(1)
    .single()
  
  return data
}

// Real-time updates (optional)
const subscription = supabase
  .channel('room_stats_changes')
  .on('postgres_changes', 
    { event: 'INSERT', schema: 'public', table: 'room_stats' },
    (payload) => {
      console.log('New count:', payload.new)
      // Update UI with new data
    }
  )
  .subscribe()
```

### Row Level Security (RLS)

Configure Supabase RLS to allow:
- **Backend**: Full read/write access using service role key (bypasses RLS)
- **Front-end**: Read-only access using anon key

```sql
-- Enable RLS on the table
ALTER TABLE room_stats ENABLE ROW LEVEL SECURITY;

-- Allow anonymous users to read all data
CREATE POLICY "Allow public read access"
  ON room_stats
  FOR SELECT
  TO anon
  USING (true);

-- Only authenticated service role can insert
-- (Service role key bypasses RLS by default)
```

### API Endpoints Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/rest/v1/room_stats` | Fetch all records | Anon |
| GET | `/rest/v1/room_stats?room_id=eq.lobby` | Fetch by room | Anon |
| GET | `/rest/v1/room_stats?order=timestamp.desc&limit=1` | Latest record | Anon |
| POST | `/rest/v1/room_stats` | Insert new record | Service |

## Error Handling

The system includes comprehensive error handling at every stage:

### Custom Exception Classes

- `EnvironmentValidationError`: Invalid or missing environment variables
- `ImageProcessingError`: Image conversion or validation failures
- `YOLOInferenceError`: YOLO model loading or inference failures
- `SupabaseConnectionError`: Database connection failures
- `SupabaseValidationError`: Invalid data before insertion
- `SupabaseInsertError`: Database insertion failures

### Retry Logic

Failed Supabase insertions are automatically retried with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay
- Final failure: Logs error and raises exception

### Logging

All operations are logged with appropriate levels:
- **INFO**: Successful operations, initialization
- **DEBUG**: Detailed processing steps (enable with `logging.DEBUG`)
- **WARNING**: Recoverable issues, unexpected values
- **ERROR**: Operation failures, exceptions

## Performance Considerations

### YOLO Model Selection

- **yolov8n.pt** (Nano): Fastest, ~6MB, good for real-time processing
- **yolov8s.pt** (Small): Balanced speed/accuracy
- **yolov8m.pt** (Medium): Better accuracy, slower
- Choose based on your hardware and latency requirements

### Optimization Tips

1. **Reuse Pipeline Instance**: Initialize once, process many images
2. **Batch Processing**: Process multiple images in sequence
3. **Image Resolution**: Resize large images before encoding to Base64
4. **Confidence Threshold**: Adjust in `config.py` to balance accuracy/performance
5. **Database Indexing**: Ensure indexes exist on frequently queried columns

## Troubleshooting

### Common Issues

**Issue**: `EnvironmentValidationError: SUPABASE_URL is not set`
- **Solution**: Create `.env` file with required variables

**Issue**: `YOLOInferenceError: Failed to load YOLO model`
- **Solution**: Ensure internet connection for first-time model download

**Issue**: `SupabaseInsertError: Failed to insert after 3 attempts`
- **Solution**: Check network connection and Supabase service status

**Issue**: `ImageProcessingError: Invalid Base64 string format`
- **Solution**: Verify Base64 string is properly encoded and not corrupted

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] Support for multiple camera sources
- [ ] Real-time streaming via WebSockets
- [ ] Historical analytics and trend analysis
- [ ] Person tracking across rooms
- [ ] Alert system for overcrowding
- [ ] API rate limiting and caching
- [ ] Docker containerization
- [ ] Kubernetes deployment configuration
- [ ] Automated testing suite
- [ ] Performance benchmarking tools

## Contributing

This is an internal project, but contributions are welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the troubleshooting section above

## Acknowledgments

- **Ultralytics**: For the excellent YOLO v8 implementation
- **Supabase**: For the developer-friendly database platform
- **OpenCV**: For robust image processing capabilities
