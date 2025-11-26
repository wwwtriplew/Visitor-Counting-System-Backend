# HTTP Ingestion Server

A Flask-based REST API server that receives images from cameras, processes them through the YOLO pipeline, and stores results in Supabase.

# Important 

do NOT use open-cv, but run
pip install opencv-python-headless

run 
pip install opencv-python-headless if necessary

## Quick Start

### 1. Install Dependencies

```bash
pip install flask python-dotenv gunicorn
```

### 2. Configure Environment

The `.env` file is already configured with:
- ✅ Supabase credentials
- ✅ Generated API key: `<<<SEE .env>>>` (ingestion_api_key)
- ✅ Server settings (host: 0.0.0.0, port: 8000)

### 3. Start the Server

**Development:**
```bash
python -m server.app
```

**Production:**
```bash
gunicorn server.app:app --bind 0.0.0.0:8000 --workers 4 --timeout 120
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Process Image (JSON)
```bash
curl -X POST http://localhost:8000/api/v1/process-image \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -d '{
    "image": "'"$(base64 -w 0 testing_images/sevenpeople.jpg)"'",
    "room_id": "test-room"
  }'
```

### Process Image (Multipart)
```bash
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -F "room_id=test-room"
```

## Testing

```bash
# Edit test_server.py and set API_KEY to: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI
python test_server.py
```

## File Structure

```
server/
├── __init__.py          # Package initialization
├── app.py              # Flask application (main server code)
├── config.py           # Configuration and environment variables
└── requirements.txt    # Server dependencies
```

## Features

- ✅ **Authentication**: API key-based security via X-API-KEY header
- ✅ **Two Endpoints**: JSON (base64) and Multipart (raw JPEG)
- ✅ **Validation**: Room ID pattern, image size limits
- ✅ **Error Handling**: Comprehensive error responses
- ✅ **Logging**: Detailed request/response logging
- ✅ **Production Ready**: Gunicorn support with multiple workers

## Configuration

All configuration is in `.env`:

```bash
# Authentication
INGESTION_API_KEY=Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI

# Network
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Processing (inherited from main app)
SUPABASE_URL=https://rgkkadtaiivcuuvekwdo.supabase.co
SUPABASE_SERVICE_KEY=<configured>
TABLE_NAME=detections
```

## Security

- **API Key**: Required in `X-API-KEY` header for all processing endpoints
- **Size Limits**: Max 10MB image, 15MB total request
- **Validation**: Room ID must match `^[A-Za-z0-9_-]{1,64}$`
- **LAN Only**: Designed for local network deployment

## Camera Integration

Cameras should POST images every 60 seconds:

**Example (bash script):**
```bash
while true; do
    curl -X POST http://server-ip:8000/api/v1/process-image-bytes \
        -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
        -F "file=@/tmp/snapshot.jpg" \
        -F "room_id=lobby"
    sleep 60
done
```

## Documentation

- **Full Deployment Guide**: See `SERVER_DEPLOYMENT.md`
- **API Specification**: See `SERVER_IMPLEMENTATION.md`

---

**Server is ready to receive images from cameras! 📸**
