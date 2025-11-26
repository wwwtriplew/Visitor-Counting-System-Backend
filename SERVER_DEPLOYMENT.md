# HTTP Ingestion Server - Deployment Guide

## Overview

The HTTP Ingestion Server provides REST API endpoints for cameras to send images for processing. It receives images via HTTP POST, processes them through the YOLO pipeline, and stores results in Supabase.

## Architecture

```
Cameras → HTTP POST → Ingestion Server → YOLO Pipeline → Supabase → Frontend
```

## Prerequisites

- Python 3.8+ installed
- Backend dependencies installed (`pip install -r requirements.txt`)
- Supabase credentials configured in `.env`
- Network access from cameras to server

## Quick Start

### 1. Install Server Dependencies

```bash
cd /workspaces/Visitor-Counting-System-Backend
pip install -r server/requirements.txt
```

### 2. Generate API Key

Generate a secure API key for camera authentication:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Configure Environment

Add to your `.env` file:

```bash
# HTTP Ingestion Server
INGESTION_API_KEY=<paste-your-generated-key-here>
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 4. Start the Server

**Development Mode:**
```bash
python -m server.app
```

**Production Mode (recommended):**
```bash
gunicorn server.app:app --bind 0.0.0.0:8000 --workers 4 --timeout 120
```

### 5. Verify Server is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ready",
  "service": "visitor-counting-ingestion-server",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check if server is running and ready

**Response:**
```json
{
  "status": "ready",
  "service": "visitor-counting-ingestion-server",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

---

### 2. Process Image (JSON)

**Endpoint:** `POST /api/v1/process-image`

**Description:** Accept base64-encoded image in JSON payload

**Headers:**
```
Content-Type: application/json
X-API-KEY: <your-api-key>
```

**Request Body:**
```json
{
  "image": "<base64_string_without_data_prefix>",
  "room_id": "room-101",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "room_id": "room-101",
  "people_count": 7,
  "processing_ms": 142,
  "timestamp": "2025-11-26T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid payload
- `401 Unauthorized` - Missing or invalid API key
- `413 Payload Too Large` - Image exceeds 10MB
- `500 Internal Server Error` - Processing failed

---

### 3. Process Image (Multipart)

**Endpoint:** `POST /api/v1/process-image-bytes`

**Description:** Accept raw JPEG file via multipart form

**Headers:**
```
Content-Type: multipart/form-data
X-API-KEY: <your-api-key>
```

**Form Fields:**
- `file`: JPEG image file (max 10MB)
- `room_id`: Room identifier (e.g., "lobby", "room-101")
- `timestamp`: Optional ISO8601 timestamp

**Response:** Same as JSON endpoint

---

## Camera Integration

### Example: cURL

```bash
# JSON endpoint
curl -X POST http://server-ip:8000/api/v1/process-image \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{
    "image": "'"$(base64 -w 0 image.jpg)"'",
    "room_id": "lobby"
  }'

# Multipart endpoint
curl -X POST http://server-ip:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: your-api-key" \
  -F "file=@image.jpg" \
  -F "room_id=lobby"
```

### Example: Python

```python
import requests
import base64

# Read image
with open('image.jpg', 'rb') as f:
    image_data = f.read()

# JSON endpoint
base64_image = base64.b64encode(image_data).decode('utf-8')
response = requests.post(
    'http://server-ip:8000/api/v1/process-image',
    headers={'X-API-KEY': 'your-api-key'},
    json={
        'image': base64_image,
        'room_id': 'lobby'
    }
)

# Multipart endpoint
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://server-ip:8000/api/v1/process-image-bytes',
        headers={'X-API-KEY': 'your-api-key'},
        files={'file': f},
        data={'room_id': 'lobby'}
    )

print(response.json())
```

## Production Deployment

### Option 1: Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 worker processes
gunicorn server.app:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
```

### Option 2: Systemd Service

Create `/etc/systemd/system/visitor-counting-server.service`:

```ini
[Unit]
Description=Visitor Counting Ingestion Server
After=network.target

[Service]
Type=notify
User=your-user
WorkingDirectory=/workspaces/Visitor-Counting-System-Backend
Environment="PATH=/workspaces/Visitor-Counting-System-Backend/venv/bin"
ExecStart=/workspaces/Visitor-Counting-System-Backend/venv/bin/gunicorn server.app:app --bind 0.0.0.0:8000 --workers 4 --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable visitor-counting-server
sudo systemctl start visitor-counting-server
sudo systemctl status visitor-counting-server
```

### Option 3: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r server/requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "server.app:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

Build and run:
```bash
docker build -t visitor-counting-server .
docker run -d \
  --name visitor-counting-server \
  -p 8000:8000 \
  --env-file .env \
  visitor-counting-server
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INGESTION_API_KEY` | **Yes** | - | API key for authentication |
| `SUPABASE_URL` | **Yes** | - | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | **Yes** | - | Supabase service role key |
| `TABLE_NAME` | No | `detections` | Database table name |
| `SERVER_HOST` | No | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | No | `8000` | Server port |

### Validation Rules

- **room_id**: Must match `^[A-Za-z0-9_-]{1,64}$`
- **image**: Max decoded size 10MB
- **timestamp**: ISO8601 format (optional)

## Testing

### Run Test Suite

```bash
# Edit test_server.py and set API_KEY
python test_server.py
```

### Manual Tests

```bash
# Health check
curl http://localhost:8000/health

# Test with tiny PNG
curl -X POST http://localhost:8000/api/v1/process-image \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "room_id": "test-room"
  }'

# Test with real image
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: your-key" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -F "room_id=test-room"
```

## Monitoring

### Check Server Logs

```bash
# If running with gunicorn
tail -f /path/to/logs/access.log
tail -f /path/to/logs/error.log

# If running as systemd service
sudo journalctl -u visitor-counting-server -f

# If running with Docker
docker logs -f visitor-counting-server
```

### Key Metrics to Monitor

- **Request rate**: Requests per minute
- **Processing time**: Average milliseconds per image
- **Error rate**: Failed requests vs total
- **People count**: Average detections per room
- **Response codes**: 200 vs 4xx/5xx

## Security Considerations

### 1. API Key Security

- **Generate strong keys**: Use `secrets.token_urlsafe(32)`
- **Rotate regularly**: Change keys periodically
- **Per-camera keys**: Consider unique keys per camera
- **Never log keys**: Ensure API keys don't appear in logs

### 2. Network Security

- **LAN only**: Server should not be exposed to internet
- **Firewall**: Only allow camera IPs to access port 8000
- **HTTPS**: Use reverse proxy (nginx) with SSL for production

### 3. Rate Limiting

Consider adding rate limiting to prevent abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('X-API-KEY'),
    default_limits=["60 per minute"]
)
```

## Troubleshooting

### Server won't start

**Error:** `INGESTION_API_KEY environment variable must be set`
- **Solution:** Add `INGESTION_API_KEY` to `.env` file

**Error:** `Failed to initialize pipeline`
- **Solution:** Verify Supabase credentials in `.env`

### Cameras can't reach server

**Check network:**
```bash
# Get server IP
ip addr show

# Test from camera network
ping server-ip
curl http://server-ip:8000/health
```

**Check firewall:**
```bash
# Allow port 8000
sudo ufw allow 8000
```

### Processing is slow

**Solutions:**
- Increase gunicorn workers: `--workers 8`
- Use faster YOLO model: `yolov8n.pt`
- Add more RAM/CPU to server
- Process images at lower resolution

### Authentication fails

**Error:** `401 Unauthorized`
- **Solution:** Verify `X-API-KEY` header matches `.env`
- Check API key has no extra whitespace

### Images too large

**Error:** `413 Payload Too Large`
- **Solution:** Cameras should resize images before sending
- Recommended: 640x480 or 1280x720
- Compress JPEG quality to 85-90%

## Performance Optimization

### 1. Worker Configuration

```bash
# Calculate optimal workers
workers = (2 x CPU cores) + 1

# For 4 CPU cores:
gunicorn server.app:app --workers 9 --timeout 120
```

### 2. Image Processing

- **Resize images**: 640x480 is sufficient for person detection
- **JPEG compression**: Quality 85-90 reduces size without accuracy loss
- **Batch processing**: Group multiple images if possible

### 3. Database Optimization

- Ensure Supabase indexes exist on `timestamp` and `room_id`
- Use connection pooling (handled by Supabase client)

## Camera Configuration

### Recommended Settings

- **Image size**: 640x480 or 1280x720
- **Format**: JPEG with quality 85-90
- **Frequency**: 1 image per minute (or as needed)
- **Endpoint**: Use multipart for efficiency
- **Timeout**: 30 seconds
- **Retry**: 3 attempts with exponential backoff

### Example Camera Script

```bash
#!/bin/bash
# Camera script to capture and send image

API_KEY="your-api-key"
SERVER_URL="http://server-ip:8000"
ROOM_ID="lobby"

while true; do
    # Capture image (adjust for your camera)
    ffmpeg -i /dev/video0 -frames 1 -q:v 85 /tmp/snapshot.jpg
    
    # Send to server
    curl -X POST "$SERVER_URL/api/v1/process-image-bytes" \
        -H "X-API-KEY: $API_KEY" \
        -F "file=@/tmp/snapshot.jpg" \
        -F "room_id=$ROOM_ID"
    
    # Wait 60 seconds
    sleep 60
done
```

## Maintenance

### Regular Tasks

- **Monitor logs**: Check for errors daily
- **Rotate API keys**: Change keys quarterly
- **Update dependencies**: `pip install --upgrade -r requirements.txt`
- **Check disk space**: Logs can grow large
- **Verify Supabase data**: Ensure counts are reasonable

### Backup Strategy

- **Code**: Already in Git
- **Configuration**: Backup `.env` securely (encrypted)
- **Logs**: Archive logs older than 30 days
- **Database**: Supabase handles backups automatically

---

**Server is ready to receive images from cameras! 📸**

For support, check logs and refer to the troubleshooting section.
