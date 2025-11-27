# Visitor Counting System - Backend API

> **Production-ready backend system for real-time visitor monitoring using YOLO v8 object detection and Supabase**

A sophisticated backend implementation that processes camera images to count people in real-time, designed for monitoring visitor distribution across multiple rooms in a building.

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [HTTP Ingestion Server](#http-ingestion-server)
  - [Python Processing Pipeline](#python-processing-pipeline)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Performance & Optimization](#performance--optimization)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Overview

### What This System Does

1. **Receives** images from cameras (Base64 encoded or raw JPEG)
2. **Processes** images using YOLO v8 to detect and count people
3. **Stores** results in Supabase database
4. **Provides** REST API endpoints for camera integration
5. **Enables** real-time monitoring via frontend applications

### Key Features

✅ **Two Integration Methods:**
- HTTP REST API for camera integration
- Python SDK for custom implementations

✅ **Production-Ready:**
- Comprehensive error handling with custom exceptions
- Automatic retry logic with exponential backoff
- Input validation at every stage
- Detailed logging for monitoring

✅ **Optimized Performance:**
- Model instance caching (process multiple images efficiently)
- Configurable confidence thresholds
- Lightweight YOLO nano model (~6MB)

✅ **Secure:**
- API key authentication for HTTP endpoints
- Row Level Security (RLS) configuration for frontend access
- Service role key isolation

---

## System Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Cameras   │ ─POST─→ │  HTTP Ingestion  │ ─SDK─→  │   Backend    │
│  (ESP32)    │         │      Server      │         │   Pipeline   │
└─────────────┘         └──────────────────┘         └──────┬───────┘
                                                             │
                                                             ↓
                        ┌─────────────────────────────────────────┐
                        │           YOLO v8 Processing            │
                        │  • Load image from Base64/bytes         │
                        │  • Run person detection inference       │
                        │  • Count people (confidence > 0.5)      │
                        └─────────────┬───────────────────────────┘
                                      │
                                      ↓
                        ┌──────────────────────────┐
                        │   Supabase PostgreSQL    │
                        │  • Store detection data  │
                        │  • Provide REST API      │
                        │  • Enable real-time subs │
                        └──────────┬───────────────┘
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │  Frontend (Web App)  │
                        │  • Fetch latest data │
                        │  • Display occupancy │
                        └──────────────────────┘
```

### Data Flow

```
Image Capture → Base64 Encoding → HTTP POST → 
Server Receives → Validation → YOLO Inference → 
People Count → Database Insert → Frontend Display
```

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Supabase account (free tier available)
- ~500MB disk space (for dependencies + YOLO model)

### 1. Installation

```bash
# Clone repository
git clone https://github.com/wwwtriplew/Visitor-Counting-System-Backend.git
cd Visitor-Counting-System-Backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

Create table in Supabase SQL Editor:

```sql
CREATE TABLE detections (
  id BIGSERIAL PRIMARY KEY,
  room_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  people_count INT NOT NULL,
  CONSTRAINT people_count_non_negative CHECK (people_count >= 0)
);

-- Indexes for performance
CREATE INDEX idx_detections_room_id ON detections(room_id);
CREATE INDEX idx_detections_timestamp ON detections(timestamp DESC);
CREATE INDEX idx_detections_room_timestamp ON detections(room_id, timestamp DESC);
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required settings:

```bash
# Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# HTTP server API key (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
INGESTION_API_KEY=your-secure-api-key-here

# Optional: Database table name (default: detections)
TABLE_NAME=detections
```

### 4. Start HTTP Server

```bash
# Development mode
python -m server.app

# Production mode (recommended)
gunicorn server.app:app --bind 0.0.0.0:8000 --workers 4 --timeout 120
```

### 5. Test the Server

```bash
# Health check
curl http://localhost:8000/health

# Test with image (replace with your API key)
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: your-api-key-here" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -F "room_id=test-room"
```

Expected response:

```json
{
  "status": "ok",
  "room_id": "test-room",
  "people_count": 10,
  "timestamp": "2025-11-27T14:24:57.447492",
  "processing_ms": 641
}
```

---
---
---

## API Reference a

### HTTP Ingestion Server

The HTTP server provides REST endpoints for camera integration. Perfect for ESP32 cameras, Raspberry Pi, or any device that can send HTTP requests.

#### Endpoint 1: Health Check

**No authentication required**

### 📥 Input Format

```
Method: GET
URL: /health
Authentication: None
Headers: None required
Body: None
Query Parameters: None
```

**Complete Request Specification:**

```http
GET /health HTTP/1.1
Host: your-server:8000
```

**Constraints:**
- No rate limiting
- No authentication required
- Can be used for uptime monitoring
- Returns JSON response

**Response:**

```json
{
  "service": "visitor-counting-ingestion-server",
  "status": "ready",
  "timestamp": "2025-11-27T14:17:35.601951Z"
}
```

---

#### Endpoint 2: Process Image (Multipart Upload) - **RECOMMENDED**

**For cameras sending JPEG files directly**

### 📥 Input Format

```
Method: POST
URL: /api/v1/process-image-bytes
Authentication: Required (X-API-KEY header)
Content-Type: multipart/form-data (auto-generated, DO NOT set manually)

Headers:
  X-API-KEY: <your-api-key> (Required, String, 32+ characters)

Body (multipart/form-data):
  file: <binary-jpeg-image> (Required, File, max 10MB, JPEG format)
  room_id: <room-identifier> (Required, String, 1-64 chars, alphanumeric + dash/underscore)

Query Parameters: None
```

**Complete Request Specification:**

```http
POST /api/v1/process-image-bytes HTTP/1.1
Host: your-server:8000
X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="room_id"

lobby
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="snapshot.jpg"
Content-Type: image/jpeg

[binary JPEG image data]
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

**Field Constraints:**

| Field | Type | Required | Constraints | Example |
|-------|------|----------|-------------|----------|
| `file` | Binary File | ✅ Yes | JPEG format, max 10MB | snapshot.jpg |
| `room_id` | String | ✅ Yes | Pattern: `^[A-Za-z0-9_-]{1,64}$` | "lobby" or "room-101" |
| `X-API-KEY` | Header | ✅ Yes | Exact match with server config | "Z8xN7vK2pQ9..." |

**Validation Rules:**
- **Image file**: Must be valid JPEG, max 10MB (10,485,760 bytes)
- **room_id**: Only alphanumeric characters, hyphens (-), and underscores (_) allowed
- **room_id length**: Minimum 1 character, maximum 64 characters
- **API Key**: Case-sensitive, must match `INGESTION_API_KEY` in server config

**⚠️ Important: Content-Type Explanation**

**DO NOT manually set** `Content-Type: multipart/form-data` when using HTTP clients, webhooks, or programming libraries. The `Content-Type` header with the correct `boundary` parameter is **automatically generated** by your HTTP client.

**What is multipart/form-data?**
- A special encoding format for uploading files via HTTP
- Allows sending both binary data (images) and text data (room_id) in one request
- Requires a unique `boundary` string to separate different parts of the form data

**How to use correctly:**

| Tool/Library | Correct Usage | ❌ Wrong Usage |
|--------------|---------------|----------------|
| **cURL** | `-F "file=@image.jpg"` (auto-generates Content-Type) | `-H "Content-Type: multipart/form-data"` |
| **Postman** | Select "form-data" in Body tab (auto-generates) | Manually add Content-Type header |
| **Python requests** | `files={"file": f}` (auto-generates) | `headers={"Content-Type": "multipart/form-data"}` |
| **JavaScript fetch** | Use `FormData()` object (auto-generates) | Manually set Content-Type |
| **Webhooks** | Use form-data fields, not JSON | Send as `application/json` |

**Why the boundary matters:**
```http
POST /api/v1/process-image-bytes HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
X-API-KEY: your-key

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="room_id"

lobby
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="snapshot.jpg"
Content-Type: image/jpeg

[binary image data]
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

The `boundary` string (e.g., `----WebKitFormBoundary7MA4YWxkTrZu0gW`) separates each field. Your HTTP client automatically:
1. Generates a unique boundary string
2. Adds it to the Content-Type header
3. Uses it to wrap each form field

**Request Body (form-data fields):**

```
file: [Binary JPEG image, max 10MB]
room_id: [Room identifier, alphanumeric + dash/underscore, max 64 chars]
```

**Example (cURL):**

```bash
# ✅ CORRECT: Use -F flag (automatically handles Content-Type)
curl -X POST http://your-server:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@snapshot.jpg" \
  -F "room_id=lobby"

# ❌ WRONG: Don't manually add Content-Type header
# curl -X POST http://your-server:8000/api/v1/process-image-bytes \
#   -H "Content-Type: multipart/form-data" \  # <-- DO NOT DO THIS
#   -H "X-API-KEY: your-key" \
#   -F "file=@snapshot.jpg" \
#   -F "room_id=lobby"
```

**Example (Python requests):**

```python
import requests

url = "http://your-server:8000/api/v1/process-image-bytes"

# ✅ CORRECT: Only set X-API-KEY, let requests handle Content-Type
headers = {"X-API-KEY": "your-api-key-here"}

with open("snapshot.jpg", "rb") as f:
    files = {"file": f}
    data = {"room_id": "lobby"}
    response = requests.post(url, headers=headers, files=files, data=data)

print(response.json())

# ❌ WRONG: Don't manually set Content-Type
# headers = {
#     "X-API-KEY": "your-key",
#     "Content-Type": "multipart/form-data"  # <-- DO NOT DO THIS
# }
```

**Example (ESP32 Arduino):**

```cpp
#include <HTTPClient.h>

void sendImage() {
  HTTPClient http;
  http.begin("http://192.168.1.100:8000/api/v1/process-image-bytes");
  http.addHeader("X-API-KEY", "your-api-key-here");
  
  // Capture image from camera (pseudo-code)
  uint8_t* imageBuffer;
  size_t imageSize;
  captureImage(&imageBuffer, &imageSize);
  
  // Create multipart form data
  String boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW";
  String body = "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"room_id\"\r\n\r\n";
  body += "lobby\r\n";
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n";
  body += "Content-Type: image/jpeg\r\n\r\n";
  
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  
  int httpCode = http.POST((uint8_t*)body.c_str(), body.length() + imageSize);
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("Success: " + response);
  }
  
  http.end();
}
```

**Success Response:**

```json
{
  "status": "ok",
  "room_id": "lobby",
  "people_count": 7,
  "timestamp": "2025-11-27T14:24:57.447492",
  "processing_ms": 641
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Missing API key | No `X-API-KEY` header provided |
| 401 | Invalid API key | API key doesn't match server configuration |
| 400 | Missing room_id | `room_id` field not provided |
| 400 | Invalid room_id format | Must match `^[A-Za-z0-9_-]{1,64}$` |
| 400 | Missing image file | No file uploaded |
| 413 | Image too large | Image exceeds 10MB limit |
| 500 | Processing failed | YOLO inference or database error |

**Example Error Response:**

```json
{
  "error": "Missing API key",
  "message": "X-API-KEY header is required"
}
```

---

#### Endpoint 3: Process Image (JSON Base64)

**For systems already encoding images as Base64**

### 📥 Input Format

```
Method: POST
URL: /api/v1/process-image
Authentication: Required (X-API-KEY header)
Content-Type: application/json (Required, must set manually)

Headers:
  Content-Type: application/json (Required)
  X-API-KEY: <your-api-key> (Required, String, 32+ characters)

Body (raw JSON):
{
  "image": "<base64-encoded-jpeg-string>",  (Required, String, base64-encoded JPEG)
  "room_id": "<room-identifier>"            (Required, String, 1-64 chars, alphanumeric + dash/underscore)
}

Query Parameters: None
```

**Complete Request Specification:**

```http
POST /api/v1/process-image HTTP/1.1
Host: your-server:8000
Content-Type: application/json
X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI

{
  "image": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a...",
  "room_id": "conference-room-a"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints | Example |
|-------|------|----------|-------------|----------|
| `image` | String | ✅ Yes | Base64-encoded JPEG, decoded size max 10MB | "/9j/4AAQSkZJ..." |
| `room_id` | String | ✅ Yes | Pattern: `^[A-Za-z0-9_-]{1,64}$` | "conference-room-a" |
| `Content-Type` | Header | ✅ Yes | Must be "application/json" | "application/json" |
| `X-API-KEY` | Header | ✅ Yes | Exact match with server config | "Z8xN7vK2pQ9..." |

**Validation Rules:**
- **image**: Must be valid base64 string encoding a JPEG image
- **image size**: Decoded binary must be ≤ 10MB (10,485,760 bytes)
- **room_id**: Only alphanumeric characters, hyphens (-), and underscores (_) allowed
- **room_id length**: Minimum 1 character, maximum 64 characters
- **JSON**: Must be valid JSON format
- **API Key**: Case-sensitive, must match `INGESTION_API_KEY` in server config

**How to generate base64:**
```bash
# Command line (Linux/Mac)
base64 -w 0 image.jpg  # Output: single-line base64 string

# Python
import base64
with open("image.jpg", "rb") as f:
    base64_string = base64.b64encode(f.read()).decode("utf-8")

# JavaScript
const base64 = await new Promise((resolve) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result.split(',')[1]);
  reader.readAsDataURL(file);
});
```

**Request Body:**

```json
{
  "image": "base64-encoded-jpeg-string-here",
  "room_id": "conference-room-a"
}
```

**Example (Python):**

```python
import base64
import requests

# Read and encode image
with open("snapshot.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# Send request
url = "http://your-server:8000/api/v1/process-image"
headers = {
    "Content-Type": "application/json",
    "X-API-KEY": "your-api-key-here"
}
payload = {
    "image": image_base64,
    "room_id": "conference-room-a"
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

**Example (JavaScript - for multipart):**

```javascript
// ✅ CORRECT: Use FormData for multipart uploads
async function sendImageMultipart(imageFile, roomId) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('room_id', roomId);
  
  const response = await fetch('http://your-server:8000/api/v1/process-image-bytes', {
    method: 'POST',
    headers: {
      'X-API-KEY': 'your-api-key-here'
      // DO NOT set Content-Type here - FormData handles it automatically
    },
    body: formData
  });
  
  const result = await response.json();
  console.log('People count:', result.people_count);
}

// ❌ WRONG: Manually setting Content-Type breaks multipart
// const response = await fetch('http://your-server:8000/api/v1/process-image-bytes', {
//   method: 'POST',
//   headers: {
//     'Content-Type': 'multipart/form-data',  // <-- DO NOT DO THIS
//     'X-API-KEY': 'your-key'
//   },
//   body: formData
// });

// Usage:
const fileInput = document.getElementById('imageInput');
const file = fileInput.files[0];
sendImageMultipart(file, 'lobby');
```

**Example (JavaScript - for base64/JSON):**

```javascript
// Use this for the JSON endpoint (/api/v1/process-image)
async function sendImageBase64(imageFile, roomId) {
  const reader = new FileReader();
  
  reader.onload = async () => {
    const base64 = reader.result.split(',')[1]; // Remove data:image/jpeg;base64,
    
    const response = await fetch('http://your-server:8000/api/v1/process-image', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',  // ✅ CORRECT for JSON endpoint
        'X-API-KEY': 'your-api-key-here'
      },
      body: JSON.stringify({
        image: base64,
        room_id: roomId
      })
    });
    
    const result = await response.json();
    console.log('People count:', result.people_count);
  };
  
  reader.readAsDataURL(imageFile);
}
```

**Response:** Same format as multipart endpoint

---

### 📌 **Webhook Configuration Guide**

**If you're using a webhook service (Zapier, Make.com, n8n, etc.):**

1. **Choose the correct endpoint:**
   - For file upload: Use `/api/v1/process-image-bytes` with form-data
   - For JSON: Use `/api/v1/process-image` with base64-encoded image

2. **Common webhook mistakes:**

   ❌ **WRONG - Trying to send files as JSON:**
   ```json
   {
     "file": "[object File]",
     "room_id": "lobby"
   }
   ```
   
   ✅ **CORRECT - Use form-data fields:**
   ```
   Form Field 1: room_id = lobby
   Form Field 2: file = [upload file]
   ```

3. **Webhook setup example (generic):**
   ```
   URL: http://your-server:8000/api/v1/process-image-bytes
   Method: POST
   Content Type: multipart/form-data (or "Form Data" in UI)
   
   Headers:
     X-API-KEY: your-api-key-here
   
   Body (Form Data):
     room_id: lobby
     file: [select file from previous step]
   ```

4. **Testing webhook integration:**
   ```bash
   # First, test with cURL to ensure your server is working
   curl -X POST http://your-server:8000/api/v1/process-image-bytes \
     -H "X-API-KEY: your-key" \
     -F "file=@test.jpg" \
     -F "room_id=test"
   
   # If cURL works but webhook fails:
   # - Check if webhook service sends form-data correctly
   # - Verify API key is passed in headers (not body)
   # - Ensure room_id is sent as form field (not in URL params)
   ```

---

### Python Processing Pipeline

For custom integrations, direct Python SDK usage, or batch processing.

#### Initialize Pipeline (Recommended)

**Reuse model instance for multiple images:**

```python
from backend.process_images import ImageProcessingPipeline

# Initialize once (loads YOLO model, connects to Supabase)
pipeline = ImageProcessingPipeline(
    supabase_url="https://your-project.supabase.co",
    supabase_service_key="your-service-key",
    table_name="detections"  # Optional, defaults to "detections"
)

# Process multiple images efficiently
for image_data, room in camera_queue:
    result = pipeline.process_image(
        base64_image=image_data,
        room_id=room
    )
    
    if result["success"]:
        print(f"✓ {room}: {result['people_count']} people")
    else:
        print(f"✗ {room}: {result['error']}")
```

**Return Value:**

```python
{
    "success": True,  # or False
    "room_id": "lobby",
    "people_count": 7,
    "timestamp": "2025-11-27T14:30:00.123456",
    "error": None  # or error message if success=False
}
```

---

#### Process Single Image

**For one-off processing (less efficient for batch):**

```python
from backend.process_images import process_image

result = process_image(
    base64_image="your-base64-encoded-image",
    room_id="test-room"
)

if result["success"]:
    print(f"Detected {result['people_count']} people")
    print(f"Timestamp: {result['timestamp']}")
else:
    print(f"Error: {result['error']}")
```

---

#### Advanced Usage: Custom Configuration

```python
from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env

# Load environment variables
config = load_and_validate_env()

# Initialize with custom settings
pipeline = ImageProcessingPipeline(
    supabase_url=config["SUPABASE_URL"],
    supabase_service_key=config["SUPABASE_SERVICE_KEY"],
    model_path="yolov8s.pt",  # Use small model instead of nano
    table_name="custom_detections"
)

# Process with custom timestamp
from datetime import datetime

result = pipeline.process_image(
    base64_image=image_data,
    room_id="lobby",
    timestamp=datetime(2025, 11, 27, 14, 30, 0)  # Custom timestamp
)
```

---

#### Command Line Interface

**For testing or cron jobs:**

```bash
# Basic usage (uses current timestamp)
python -m backend.process_images "$(base64 -i snapshot.jpg)" "lobby"

# With custom timestamp
python -m backend.process_images \
  "$(base64 -i snapshot.jpg)" \
  "lobby" \
  "2025-11-27T14:30:00"

# From Base64 file
python -m backend.process_images "$(cat image.b64)" "conference-room"
```

**Output:**

```
INFO - Validating environment configuration...
INFO - Initializing Image Processing Pipeline...
INFO - Loading YOLO model from yolov8n.pt...
INFO - YOLO model loaded successfully
INFO - Processing image for room 'lobby'...
INFO - Detected 7 people with confidence > 0.5
INFO - Storing count in database...
INFO - Successfully inserted record into detections table

✓ Successfully processed image for room 'lobby'
  Timestamp: 2025-11-27T14:30:00.123456
  People count: 7
```

---

## Database Schema

### Table: `detections`

```sql
CREATE TABLE detections (
  id BIGSERIAL PRIMARY KEY,
  room_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  people_count INT NOT NULL,
  CONSTRAINT people_count_non_negative CHECK (people_count >= 0)
);

-- Performance indexes
CREATE INDEX idx_detections_room_id ON detections(room_id);
CREATE INDEX idx_detections_timestamp ON detections(timestamp DESC);
CREATE INDEX idx_detections_room_timestamp ON detections(room_id, timestamp DESC);
```

### Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY, AUTO INCREMENT | Unique record identifier |
| `room_id` | TEXT | NOT NULL, pattern: `^[A-Za-z0-9_-]{1,64}$` | Room identifier (e.g., "lobby", "room-101") |
| `timestamp` | TIMESTAMPTZ | NOT NULL, ISO 8601 format | Detection timestamp with timezone |
| `people_count` | INT | NOT NULL, >= 0, <= 1000 | Number of people detected |

### Row Level Security (RLS)

**Backend (service role key):** Full access (bypasses RLS)

**Frontend (anon key):** Read-only access

```sql
-- Enable RLS
ALTER TABLE detections ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow anonymous read access"
  ON detections
  FOR SELECT
  TO anon
  USING (true);

-- Service role bypasses RLS automatically
```

### Example Queries

**Get latest detection for all rooms:**

```sql
SELECT DISTINCT ON (room_id) 
  room_id, 
  timestamp, 
  people_count
FROM detections
ORDER BY room_id, timestamp DESC;
```

**Get room history (last 24 hours):**

```sql
SELECT room_id, timestamp, people_count
FROM detections
WHERE room_id = 'lobby'
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

**Get average occupancy per hour:**

```sql
SELECT 
  room_id,
  DATE_TRUNC('hour', timestamp) as hour,
  AVG(people_count) as avg_count
FROM detections
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY room_id, hour
ORDER BY room_id, hour DESC;
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | ✅ Yes | - | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | ✅ Yes | - | Service role key (backend only!) |
| `INGESTION_API_KEY` | ✅ Yes* | - | API key for HTTP endpoints (*required for server) |
| `TABLE_NAME` | No | `detections` | Database table name |
| `YOLO_MODEL_PATH` | No | `yolov8n.pt` | YOLO model file path |
| `SERVER_HOST` | No | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | No | `8000` | Server port |

### Backend Configuration

Edit `backend/config.py` to customize:

```python
# YOLO settings
YOLO_CONFIDENCE_THRESHOLD = 0.5  # Detection confidence (0.0-1.0)
PERSON_CLASS_ID = 0              # COCO dataset person class

# Validation
MAX_IMAGE_SIZE = 10 * 1024 * 1024      # 10MB max image size
MAX_PEOPLE_COUNT = 1000                 # Maximum reasonable count
VALID_ROOM_ID_PATTERN = r'^[A-Za-z0-9_-]+$'

# Retry logic
MAX_RETRY_ATTEMPTS = 3           # Database insert retries
RETRY_DELAY_SECONDS = 2          # Initial retry delay
```

### Server Configuration

Edit `server/config.py` for HTTP server settings:

```python
# Image limits
MAX_IMAGE_BYTES = 10 * 1024 * 1024       # 10MB
MAX_CONTENT_LENGTH = 15 * 1024 * 1024    # 15MB (overhead)

# Validation
ROOM_ID_PATTERN = r'^[A-Za-z0-9_-]{1,64}$'
```

---

## Usage Examples

### Example 1: Camera Integration Script

**Continuous monitoring (run on camera device):**

```python
import time
import base64
import requests
from datetime import datetime

SERVER_URL = "http://192.168.1.100:8000/api/v1/process-image-bytes"
API_KEY = "your-api-key-here"
ROOM_ID = "lobby"
INTERVAL = 60  # seconds

def capture_and_send():
    # Capture image (pseudo-code, depends on your camera)
    image_path = capture_camera_image()
    
    with open(image_path, "rb") as f:
        response = requests.post(
            SERVER_URL,
            headers={"X-API-KEY": API_KEY},
            files={"file": f},
            data={"room_id": ROOM_ID}
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"[{datetime.now()}] {ROOM_ID}: {result['people_count']} people")
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Main loop
while True:
    try:
        capture_and_send()
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(INTERVAL)
```

---

### Example 2: Batch Processing

**Process multiple images from directory:**

```python
import os
import base64
from backend.process_images import ImageProcessingPipeline

# Initialize pipeline once
pipeline = ImageProcessingPipeline(
    supabase_url="https://your-project.supabase.co",
    supabase_service_key="your-key"
)

# Process all images in directory
image_dir = "/path/to/camera/snapshots"
room_id = "lobby"

for filename in os.listdir(image_dir):
    if filename.endswith(".jpg"):
        filepath = os.path.join(image_dir, filename)
        
        # Read and encode image
        with open(filepath, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Process
        result = pipeline.process_image(image_base64, room_id)
        
        if result["success"]:
            print(f"✓ {filename}: {result['people_count']} people")
        else:
            print(f"✗ {filename}: {result['error']}")
```

---

### Example 3: Real-Time Frontend Integration

**Fetch latest data for display (JavaScript):**

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://your-project.supabase.co',
  'your-anon-key-here'  // NOT service key!
)

// Get latest count for all rooms
async function getLatestCounts() {
  const { data, error } = await supabase
    .from('detections')
    .select('room_id, timestamp, people_count')
    .order('timestamp', { ascending: false })
    .limit(100)
  
  if (error) {
    console.error('Error:', error)
    return []
  }
  
  // Group by room_id, keep only latest
  const latestByRoom = {}
  data.forEach(record => {
    if (!latestByRoom[record.room_id]) {
      latestByRoom[record.room_id] = record
    }
  })
  
  return Object.values(latestByRoom)
}

// Get specific room
async function getRoomCount(roomId) {
  const { data, error } = await supabase
    .from('detections')
    .select('*')
    .eq('room_id', roomId)
    .order('timestamp', { ascending: false })
    .limit(1)
    .single()
  
  return data
}

// Real-time subscription
const subscription = supabase
  .channel('detections_channel')
  .on('postgres_changes', 
    { event: 'INSERT', schema: 'public', table: 'detections' },
    (payload) => {
      console.log('New detection:', payload.new)
      updateUI(payload.new)
    }
  )
  .subscribe()

// Usage
getLatestCounts().then(rooms => {
  rooms.forEach(room => {
    console.log(`${room.room_id}: ${room.people_count} people`)
  })
})
```

---

## Error Handling

### Custom Exception Classes

The system uses specific exceptions for different failure scenarios:

```python
from backend.utils.env_utils import EnvironmentValidationError
from backend.utils.image_utils import ImageProcessingError
from backend.utils.yolo_utils import YOLOInferenceError
from backend.utils.supabase_utils import (
    SupabaseConnectionError,
    SupabaseValidationError,
    SupabaseInsertError
)

try:
    result = pipeline.process_image(image_data, room_id)
except EnvironmentValidationError as e:
    print(f"Configuration error: {e}")
except ImageProcessingError as e:
    print(f"Invalid image: {e}")
except YOLOInferenceError as e:
    print(f"Detection failed: {e}")
except SupabaseInsertError as e:
    print(f"Database error: {e}")
```

### Retry Logic

Database insertions automatically retry with exponential backoff:

```
Attempt 1: Immediate
Attempt 2: 2 seconds delay
Attempt 3: 4 seconds delay
Final: Raise SupabaseInsertError
```

### Logging

Enable detailed logging:

```python
import logging

# Set log level
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger('backend.process_images').setLevel(logging.DEBUG)
logging.getLogger('backend.utils.yolo_utils').setLevel(logging.INFO)
```

**Log levels:**
- `DEBUG`: Detailed processing steps, detection details
- `INFO`: Successful operations, initialization
- `WARNING`: Recoverable issues, retries
- `ERROR`: Operation failures, exceptions

---

## Performance & Optimization

### YOLO Model Selection

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `yolov8n.pt` | 6MB | Fastest | Good | Real-time processing (recommended) |
| `yolov8s.pt` | 22MB | Fast | Better | Balance speed/accuracy |
| `yolov8m.pt` | 52MB | Medium | Best | High accuracy needs |

**Change model:**

```bash
# In .env file
YOLO_MODEL_PATH=yolov8s.pt
```

### Confidence Threshold Tuning

**Adjust detection sensitivity:**

```python
# In backend/config.py
YOLO_CONFIDENCE_THRESHOLD = 0.3  # More detections (may include false positives)
YOLO_CONFIDENCE_THRESHOLD = 0.7  # Fewer detections (higher confidence only)
```

**Trade-offs:**
- **Lower (0.3-0.4)**: Detects more people, including partially visible
- **Higher (0.6-0.8)**: Only high-confidence detections, may miss some people
- **Default (0.5)**: Balanced approach

### Performance Tips

1. **Reuse Pipeline Instance**
   ```python
   # ✓ GOOD: Initialize once
   pipeline = ImageProcessingPipeline(...)
   for image in images:
       pipeline.process_image(image, room)
   
   # ✗ BAD: Initialize every time
   for image in images:
       result = process_image(image, room)  # Reloads model each time!
   ```

2. **Image Resolution**
   - YOLO automatically resizes to 640x640
   - Sending high-res images wastes bandwidth
   - Resize to 1280x720 or 1920x1080 before encoding

3. **Database Indexing**
   - Ensure indexes exist (see Database Schema section)
   - Query specific rooms instead of full table scans

4. **Server Configuration**
   ```bash
   # Use multiple workers for production
   gunicorn server.app:app \
     --bind 0.0.0.0:8000 \
     --workers 4 \              # CPU cores
     --timeout 120 \            # Allow time for YOLO processing
     --worker-class sync        # Synchronous workers
   ```

---

## Troubleshooting

### Issue: Import Errors (Pylance)

**Symptoms:**
- VS Code shows red underlines on imports
- Server runs fine despite errors

**Cause:** Pylance hasn't detected virtual environment

**Solution:**

```bash
# Reload VS Code window
Ctrl+Shift+P → "Developer: Reload Window"

# Or manually select interpreter
Ctrl+Shift+P → "Python: Select Interpreter" → Choose ./venv/bin/python

# Or restart Pylance
Ctrl+Shift+P → "Pylance: Restart Language Server"
```

---

### Issue: YOLO Model Download Fails

**Symptoms:**
```
YOLOInferenceError: Failed to load YOLO model from yolov8n.pt
```

**Cause:** First-time download requires internet connection

**Solution:**

```bash
# Manual download
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# Or use different model location
echo "YOLO_MODEL_PATH=/path/to/yolov8n.pt" >> .env
```

---

### Issue: Database Connection Timeout

**Symptoms:**
```
SupabaseInsertError: Failed to insert after 3 attempts
```

**Causes:**
1. Invalid Supabase credentials
2. Network connectivity issues
3. Supabase project paused (free tier inactivity)

**Solution:**

```bash
# Test connection
python -c "
from supabase import create_client
client = create_client('YOUR_URL', 'YOUR_KEY')
print(client.table('detections').select('*').limit(1).execute())
"

# Check Supabase dashboard for project status
# Verify credentials in .env match Supabase settings
```

---

### Issue: API 401 Unauthorized

**Symptoms:**
```json
{"error": "Invalid API key", "message": "The provided API key is not valid"}
```

**Solution:**

```bash
# Verify API key in server .env matches request header
grep INGESTION_API_KEY .env

# Generate new key if needed
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env and restart server
```

---

### Issue: People Count Seems Low

**Symptoms:** Detecting fewer people than actually in image

**Causes:**
- Confidence threshold too high
- People partially occluded
- Poor lighting or image quality

**Solutions:**

```python
# 1. Lower confidence threshold
# In backend/config.py:
YOLO_CONFIDENCE_THRESHOLD = 0.3  # Default is 0.5

# 2. Check detection details (enable debug logging)
import logging
logging.basicConfig(level=logging.DEBUG)

# 3. Use better camera resolution
# 4. Improve lighting conditions
# 5. Position camera to minimize occlusions
```

---

## Documentation

### Quick Reference

- **[POSTMAN_TESTS.md](POSTMAN_TESTS.md)** - Complete API testing guide with Postman
- **[SERVER_DEPLOYMENT.md](SERVER_DEPLOYMENT.md)** - Production deployment guide
- **[UBUNTU_SERVER_DEPLOYMENT.md](UBUNTU_SERVER_DEPLOYMENT.md)** - Ubuntu server setup (2,600+ lines)
- **[documents/SUPABASE_SETUP.md](documents/SUPABASE_SETUP.md)** - Database setup instructions
- **[documents/QUICKSTART.md](documents/QUICKSTART.md)** - 5-minute setup guide

### Project Structure

```
Visitor-Counting-System-Backend/
├── backend/                      # Core processing pipeline
│   ├── config.py                # Configuration constants
│   ├── process_images.py        # Main pipeline & CLI
│   └── utils/                   # Utility modules
│       ├── env_utils.py         # Environment validation
│       ├── image_utils.py       # Image processing
│       ├── yolo_utils.py        # YOLO inference
│       └── supabase_utils.py    # Database operations
├── server/                       # HTTP ingestion server
│   ├── app.py                   # Flask application
│   ├── config.py                # Server configuration
│   └── README.md                # Server documentation
├── Test/                         # Test suite
│   ├── test_pipeline.py         # Pipeline tests
│   ├── test_server.py           # Server API tests
│   └── test_with_image.py       # Integration tests
├── documents/                    # Documentation
├── testing_images/              # Sample test images
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## Tech Stack

- **Python 3.8+** - Core language
- **YOLO v8 (Ultralytics)** - Person detection
- **OpenCV** - Image processing
- **Flask** - HTTP server framework
- **Gunicorn** - Production WSGI server
- **Supabase** - PostgreSQL database + REST API
- **python-dotenv** - Environment management

---

## Contributing

This is an internal project, but contributions are welcome:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

[Specify your license here]

---

## Support

- **Issues:** [GitHub Issues](https://github.com/wwwtriplew/Visitor-Counting-System-Backend/issues)
- **Documentation:** See `documents/` folder
- **API Testing:** See `POSTMAN_TESTS.md`

---

## Acknowledgments

- **[Ultralytics](https://ultralytics.com)** - YOLO v8 implementation
- **[Supabase](https://supabase.com)** - Database platform
- **[OpenCV](https://opencv.org)** - Computer vision library

---

**🚀 System ready for production use!**

For deployment instructions, see [SERVER_DEPLOYMENT.md](SERVER_DEPLOYMENT.md)
