# Postman Testing Guide for Visitor Counting API

## Server Information

- **Base URL**: `http://localhost:8000`
- **API Key**: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`

---

## Test 1: Health Check

### Request
- **Method**: `GET`
- **URL**: `http://localhost:8000/health`
- **Headers**: None required

### Expected Response
```json
{
  "status": "ok"
}
```

### Status Code
- ✅ `200 OK`

### Postman Tests Tab
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has status field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
});

pm.test("Status is ok", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql('ok');
});
```

---

## Test 2: Process Image - Multipart (RECOMMENDED)

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image-bytes`
- **Headers**:
  - `X-API-KEY`: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- **Body**: `form-data`
  - Key: `file` | Type: `File` | Value: [Upload image file]
  - Key: `room_id` | Type: `Text` | Value: `postman-test-room`

### Expected Response
```json
{
  "status": "ok",
  "room_id": "postman-test-room",
  "people_count": 7,
  "timestamp": "2025-11-26T12:34:56.789Z",
  "processing_time_ms": 285
}
```

### Status Code
- ✅ `200 OK`

### Postman Tests Tab
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has required fields", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    pm.expect(jsonData).to.have.property('room_id');
    pm.expect(jsonData).to.have.property('people_count');
    pm.expect(jsonData).to.have.property('timestamp');
    pm.expect(jsonData).to.have.property('processing_time_ms');
});

pm.test("Status is ok", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql('ok');
});

pm.test("Room ID matches request", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.room_id).to.eql('postman-test-room');
});

pm.test("People count is a number", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.people_count).to.be.a('number');
});

pm.test("People count is non-negative", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.people_count).to.be.at.least(0);
});

pm.test("Processing time is reasonable", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.processing_time_ms).to.be.below(5000); // Less than 5 seconds
});

pm.test("Timestamp is valid ISO format", function () {
    var jsonData = pm.response.json();
    var timestamp = new Date(jsonData.timestamp);
    pm.expect(timestamp.toString()).to.not.eql('Invalid Date');
});
```

---

## Test 3: Process Image - JSON with Base64

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-API-KEY`: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- **Body**: `raw` (JSON)

```json
{
  "image": "<base64-encoded-image-here>",
  "room_id": "json-test-room"
}
```

**Note**: Get base64 string with: `base64 -w 0 testing_images/sevenpeople.jpg`

### Expected Response
```json
{
  "status": "ok",
  "room_id": "json-test-room",
  "people_count": 7,
  "timestamp": "2025-11-26T12:34:56.789Z",
  "processing_time_ms": 312
}
```

### Status Code
- ✅ `200 OK`

### Postman Tests Tab
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response structure is valid", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.all.keys('status', 'room_id', 'people_count', 'timestamp', 'processing_time_ms');
});

pm.test("People count detected", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.people_count).to.be.a('number').and.to.be.at.least(0);
});
```

---

## Test 4: Authentication - Missing API Key

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image-bytes`
- **Headers**: ❌ No `X-API-KEY` header
- **Body**: `form-data`
  - Key: `file` | Type: `File` | Value: [Any image]
  - Key: `room_id` | Type: `Text` | Value: `test`

### Expected Response
```json
{
  "error": "Invalid or missing API key"
}
```

### Status Code
- ✅ `401 Unauthorized`

### Postman Tests Tab
```javascript
pm.test("Status code is 401", function () {
    pm.response.to.have.status(401);
});

pm.test("Error message is present", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('error');
});

pm.test("Error message mentions API key", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('api key');
});
```

---

## Test 5: Authentication - Invalid API Key

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image-bytes`
- **Headers**:
  - `X-API-KEY`: `wrong-api-key-12345`
- **Body**: `form-data`
  - Key: `file` | Type: `File` | Value: [Any image]
  - Key: `room_id` | Type: `Text` | Value: `test`

### Expected Response
```json
{
  "error": "Invalid or missing API key"
}
```

### Status Code
- ✅ `401 Unauthorized`

### Postman Tests Tab
```javascript
pm.test("Status code is 401", function () {
    pm.response.to.have.status(401);
});

pm.test("Invalid key is rejected", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error).to.exist;
});
```

---

## Test 6: Validation - Missing room_id

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image-bytes`
- **Headers**:
  - `X-API-KEY`: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- **Body**: `form-data`
  - Key: `file` | Type: `File` | Value: [Any image]
  - ❌ No `room_id` field

### Expected Response
```json
{
  "error": "Missing required field: room_id"
}
```

### Status Code
- ✅ `400 Bad Request`

### Postman Tests Tab
```javascript
pm.test("Status code is 400", function () {
    pm.response.to.have.status(400);
});

pm.test("Error mentions missing field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('room_id');
});
```

---

## Test 7: Validation - Invalid room_id Format

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image-bytes`
- **Headers**:
  - `X-API-KEY`: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- **Body**: `form-data`
  - Key: `file` | Type: `File` | Value: [Any image]
  - Key: `room_id` | Type: `Text` | Value: `room@#$%^&*()` (invalid characters)

### Expected Response
```json
{
  "error": "Invalid room_id format. Must be alphanumeric with optional hyphens/underscores"
}
```

### Status Code
- ✅ `400 Bad Request`

### Postman Tests Tab
```javascript
pm.test("Status code is 400", function () {
    pm.response.to.have.status(400);
});

pm.test("Error mentions room_id format", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('room_id');
});
```

---

## Test 8: Validation - Missing Image File

### Request
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/v1/process-image-bytes`
- **Headers**:
  - `X-API-KEY`: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- **Body**: `form-data`
  - ❌ No `file` field
  - Key: `room_id` | Type: `Text` | Value: `test-room`

### Expected Response
```json
{
  "error": "No image file provided"
}
```

### Status Code
- ✅ `400 Bad Request`

### Postman Tests Tab
```javascript
pm.test("Status code is 400", function () {
    pm.response.to.have.status(400);
});

pm.test("Error mentions missing image", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('image');
});
```

---

## Test 9: Performance - Multiple Requests

### Setup
Create a Postman Collection Runner test with:
- **Iterations**: 10
- **Delay**: 1000ms (1 second between requests)

### Request
Same as Test 2 (multipart image upload)

### Postman Tests Tab
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response time is acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(3000);
});

pm.test("Consistent response structure", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.all.keys('status', 'room_id', 'people_count', 'timestamp', 'processing_time_ms');
});

// Log response time for performance tracking
console.log("Response time: " + pm.response.responseTime + "ms");
console.log("Processing time: " + pm.response.json().processing_time_ms + "ms");
```

---

## Test 10: End-to-End Data Verification

### Request
Same as Test 2 (multipart image upload)

### Postman Tests Tab
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Data saved to database", function () {
    var jsonData = pm.response.json();
    
    // Save values for verification
    pm.environment.set("last_room_id", jsonData.room_id);
    pm.environment.set("last_timestamp", jsonData.timestamp);
    pm.environment.set("last_people_count", jsonData.people_count);
});

pm.test("Response contains valid data", function () {
    var jsonData = pm.response.json();
    
    // Check all fields are properly formatted
    pm.expect(jsonData.room_id).to.be.a('string').and.to.have.lengthOf.at.least(1);
    pm.expect(jsonData.people_count).to.be.a('number');
    pm.expect(jsonData.timestamp).to.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    pm.expect(jsonData.processing_time_ms).to.be.a('number').and.to.be.above(0);
});
```

---

## Postman Environment Variables

Create a Postman Environment with these variables:

| Variable | Initial Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | Server base URL |
| `api_key` | `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI` | API authentication key |
| `test_room_id` | `postman-test` | Default room ID for tests |

Then use in requests:
- URL: `{{base_url}}/api/v1/process-image-bytes`
- Header: `X-API-KEY: {{api_key}}`
- Body: `room_id: {{test_room_id}}`

---

## Pre-request Script for All Tests

Add this to Collection level Pre-request Script:

```javascript
// Set timestamp for logging
pm.environment.set("test_timestamp", new Date().toISOString());

// Log test start
console.log("=== Test Started: " + pm.info.requestName + " ===");
console.log("Time: " + pm.environment.get("test_timestamp"));
```

---

## Collection Variables Setup

```javascript
{
  "base_url": "http://localhost:8000",
  "api_key": "Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI",
  "valid_room_id": "test-room-001",
  "invalid_room_id": "room@#$%",
  "timeout_ms": 5000
}
```

---

## Quick Test Checklist

- [ ] Test 1: Health check returns 200 OK
- [ ] Test 2: Multipart image upload works
- [ ] Test 3: JSON image upload works  
- [ ] Test 4: Missing API key returns 401
- [ ] Test 5: Invalid API key returns 401
- [ ] Test 6: Missing room_id returns 400
- [ ] Test 7: Invalid room_id format returns 400
- [ ] Test 8: Missing image returns 400
- [ ] Test 9: Performance test (10 iterations)
- [ ] Test 10: End-to-end data verification

---

## Tips for Testing

1. **Use test images**: Images are in `testing_images/sevenpeople.jpg`
2. **Check server logs**: Watch terminal running `python -m server.app`
3. **Response times**: First request is slower (YOLO model loading)
4. **Concurrent testing**: Use Collection Runner with delay between requests
5. **Data verification**: Check Supabase dashboard to verify data is saved

---

## Troubleshooting

**Server not responding?**
```bash
# Check if server is running
curl http://localhost:8000/health

# Check server logs in terminal
# Look for errors or stack traces
```

**401 Unauthorized?**
- Verify API key is exactly: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- Check header name is: `X-API-KEY` (case-sensitive)

**400 Bad Request?**
- Ensure image file is JPEG format
- Verify room_id contains only: letters, numbers, hyphens, underscores
- Check both `file` and `room_id` fields are present

**500 Internal Server Error?**
- Check server terminal for Python traceback
- Verify YOLO model is loaded
- Check Supabase credentials in `.env`
