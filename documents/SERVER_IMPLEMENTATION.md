
# implementation_server.md

> Purpose: Stand up a small HTTP ingest server on the Linux computation machine (same SSID/LAN as cameras) to accept Base64 images via POST, run the existing pipeline, and write results to Supabase. This document covers **server design, endpoints, config, security, deployment, testing, and operations**. Camera firmware setup is handled elsewhere.

---

## 1. Requirements & Assumptions

- **Network**: Cameras and the computation machine are on the **same SSID/LAN**. Cameras can reach the server IP + port.
- **Pipeline exists**: You already have `process_image(base64_image: str, room_id: str) -> dict` that: 
  - decodes Base64 → JPEG,
  - runs YOLO,
  - inserts `{room_id, ts, people_count}` into Supabase,
  - returns `{"people_count": int, "processing_ms": int, ...}`.
- **Supabase**: URL and **service role key** are configured on the server via environment variables.
- **Security**: Cameras do **not** hold Supabase keys; ingestion is authenticated via a per-device or shared API key header.
- The fixed LAN IP is known and given(but should not be hardcoded)

---

## 2. API Design (Minimal & Practical)

### 2.1 Endpoints

- `POST /api/v1/process-image`
  - Accepts JSON payload:
    ```json
    {
      "image": "<base64_string_without_data_prefix>",
      "room_id": "room-101",
      "timestamp": "optional ISO8601 UTC string"
    }
    ```
  - Headers:
    - `X-API-KEY: <ingest_api_key>`
  - Responses:
    - `200 OK`:
      ```json
      {
        "status": "ok",
        "room_id": "room-101",
        "people_count": 7,
        "processing_ms": 142,
        "ts": "2025-11-25T16:05:00Z"
      }
      ```
    - `400 Bad Request` – malformed payload / invalid Base64 / missing fields
    - `401 Unauthorized` – bad/missing `X-API-KEY`
    - `413 Payload Too Large` – image exceeds size limit
    - `500 Internal Server Error` – unexpected processing failure

- `GET /health`  
  - Returns `{"status":"ready"}` when the server, pipeline, and env are loaded.

> **Note:** Some cameras only support multipart/form-data with raw JPEG. See §2.3 for alternative payloads.

### 2.2 JSON Schema & Validation

- `room_id`: `^[A-Za-z0-9_-]{1,64}$`
- `image`: Base64 string (no newlines; no `data:image/jpeg;base64,` prefix).
- `timestamp`: optional; if absent, server uses current UTC.

**Server-side checks:**
- Enforce **max decoded size**, e.g., 10 MB (`MAX_IMAGE_BYTES`).
- Reject if Base64 decode fails.
- Reject invalid `room_id` pattern.
- Use UTC for timestamps when writing to Supabase.

### 2.3 Alternative: Multipart Form (raw JPEG)

If the camera sends JPEG bytes:

- `POST /api/v1/process-image-bytes`
  - Content-Type: `multipart/form-data`
  - Fields:
    - `file`: raw JPEG
    - `room_id`: string
    - `timestamp`: optional
  - Same auth & responses as above.

---

## 3. Implementation (FastAPI)

> FastAPI is concise, performant, and easy to validate payloads. Use `uvicorn` for serving.

### 3.1 Directory Structure
 --server/
    app.py                 # FastAPI app
    config.py              # env + constants
    requirements.txt       # flask, python-dotenv