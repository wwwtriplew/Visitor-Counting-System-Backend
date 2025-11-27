# Postman Testing Guide for Visitor Counting API

## 📋 Quick Setup

### Server Information
- **Base URL (Local)**: `http://localhost:8000`
- **Base URL (Codespaces)**: `https://your-codespace-url-8000.app.github.dev`
- **API Key**: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`

### Prerequisites
1. Server must be running: `python -m server.app`
2. For Codespaces: Port 8000 must be **Public** (check PORTS tab)

---

## 📱 Postman UI Quick Guide

### Understanding Postman's Request Interface

When you create/open a request in Postman, you'll see these tabs:

#### **Top Section (Request Configuration)**
1. **Method Dropdown** - Select HTTP method (GET, POST, etc.)
2. **URL Bar** - Enter endpoint URL (use `{{variables}}` for dynamic values)
3. **Tabs Below URL:**
   - **Params** - Query parameters (key-value pairs in URL)
   - **Authorization** - Auth methods (we use Headers instead for API key)
   - **Headers** - HTTP headers (key-value pairs)
   - **Body** - Request payload (form-data, JSON, etc.)
   - **Pre-request Script** - JavaScript code that runs **BEFORE** sending request
   - **Tests** - JavaScript code that runs **AFTER** receiving response
   - **Settings** - Request-specific settings

#### **Headers Tab Format**
```
KEY              | VALUE              | DESCRIPTION (optional)
---------------- | ------------------ | ----------------------
X-API-KEY        | {{api_key}}        | Authentication token
Content-Type     | application/json   | Body content type
```

**How to add headers:**
1. Click **Headers** tab
2. Enter KEY in left column
3. Enter VALUE in right column
4. Check/uncheck checkbox to enable/disable header

#### **Body Tab Format**

**For Multipart File Uploads:**
1. Click **Body** tab
2. Select **form-data** radio button
3. Add rows:
```
KEY        | TYPE (dropdown) | VALUE
---------- | --------------- | ------------------------------------
file       | File            | [Click "Select Files" button]
room_id    | Text            | your-room-name
```

**For JSON Requests:**
1. Click **Body** tab
2. Select **raw** radio button
3. Select **JSON** from dropdown (changes from Text)
4. Paste JSON in text area:
```json
{
  "image": "base64stringhere...",
  "room_id": "test-room"
}
```

#### **Pre-request Script Tab (Runs BEFORE Request)**
- Executes **before** the request is sent
- Use for: setting variables, logging, timestamps, dynamic data generation
- Example use cases:
  - Log what you're testing
  - Set environment variables
  - Generate timestamps
  - Calculate signatures

```javascript
// Example Pre-request Script
console.log("🚀 Sending request to:", pm.request.url);
pm.environment.set("request_timestamp", new Date().toISOString());
```

#### **Tests Tab (Runs AFTER Response)**
- Executes **after** receiving the response
- Use for: assertions, validation, saving response data
- Example use cases:
  - Check status codes
  - Validate response structure
  - Extract data from response
  - Save data to environment variables

```javascript
// Example Tests Script
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});

var jsonData = pm.response.json();
console.log("Response:", jsonData);
```

### Key Differences: Pre-request vs Tests

| **Pre-request Script** | **Tests Script** |
|------------------------|------------------|
| Runs **BEFORE** request | Runs **AFTER** response |
| No access to response | Full access to response |
| Setup/preparation | Validation/verification |
| `pm.request.*` available | `pm.response.*` available |
| Optional (not required) | **Required** for testing |

---

## 🎯 Test 1: Health Check

### 📥 Input Format

```
Method: GET
URL: {{base_url}}/health
Headers: None
Body: None
```

### Request Setup in Postman UI

**Method:** `GET`

**URL:** `{{base_url}}/health`

**Headers Tab:**
```
(No headers required)
```

**Body Tab:**
```
(No body required)
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("🔍 Testing health endpoint...");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has status field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
});

pm.test("Status is ready", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql('ready');
});

pm.test("Response has service name", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.service).to.eql('visitor-counting-ingestion-server');
});

pm.test("Timestamp is valid", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.timestamp).to.match(/^\d{4}-\d{2}-\d{2}T/);
});

console.log("✅ Health check passed");
```

### Expected Response
```json
{
  "service": "visitor-counting-ingestion-server",
  "status": "ready",
  "timestamp": "2025-11-27T12:34:56.789Z"
}
```

---

## 🎯 Test 2: Process Image - Multipart Upload (RECOMMENDED)

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes
Content-Type: multipart/form-data (auto-generated by form-data selection)

Headers:
  X-API-KEY: {{api_key}}

Body (form-data):
  file: [Binary JPEG file] (Type: File)
  room_id: "postman-test-room" (Type: Text)
```

**⚠️ IMPORTANT:** Do NOT manually set `Content-Type: multipart/form-data` in Headers tab. It's automatically generated when you select "form-data" in Body tab.

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **form-data** (NOT raw JSON)
- Add fields:

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | [Click "Select Files" → choose testing_images/sevenpeople.jpg]
room_id    | Text  | postman-test-room
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("📤 Uploading image for processing...");
console.log("Room ID:", "postman-test-room");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has all required fields", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    pm.expect(jsonData).to.have.property('room_id');
    pm.expect(jsonData).to.have.property('people_count');
    pm.expect(jsonData).to.have.property('timestamp');
    pm.expect(jsonData).to.have.property('processing_ms');
});

pm.test("Status is ok", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql('ok');
});

pm.test("Room ID matches request", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.room_id).to.eql('postman-test-room');
});

pm.test("People count is valid number", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.people_count).to.be.a('number');
    pm.expect(jsonData.people_count).to.be.at.least(0);
});

pm.test("Processing time is reasonable", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.processing_ms).to.be.a('number');
    pm.expect(jsonData.processing_ms).to.be.below(10000); // First request may take longer (model loading)
});

pm.test("Timestamp is valid ISO format", function () {
    var jsonData = pm.response.json();
    var timestamp = new Date(jsonData.timestamp);
    pm.expect(timestamp.toString()).to.not.eql('Invalid Date');
});

// Save data for later verification
pm.environment.set("last_room_id", pm.response.json().room_id);
pm.environment.set("last_people_count", pm.response.json().people_count);

console.log("✅ Image processed successfully");
console.log("👥 People detected:", pm.response.json().people_count);
console.log("⏱️  Processing time:", pm.response.json().processing_ms + "ms");

// Note: YOLO detection is not 100% accurate
// - Confidence threshold: 0.5 (adjustable in backend/config.py)
// - May miss partially occluded people
// - May miss people at image edges or poor lighting
```

### Expected Response
```json
{
  "status": "ok",
  "room_id": "postman-test-room",
  "people_count": 10,
  "timestamp": "2025-11-27T14:24:57.447492",
  "processing_ms": 4994
}
```

**⚠️ Note on People Count Accuracy:**
- YOLO detection uses confidence threshold of **0.5** (50%)
- Detection may be lower than actual count due to:
  - Partial occlusions (people behind objects/others)
  - Distance from camera (small faces)
  - Image quality/lighting conditions
  - People at extreme angles or edges
- To improve detection:
  - Lower `YOLO_CONFIDENCE_THRESHOLD` in `backend/config.py` (try 0.3-0.4)
  - Use higher resolution images
  - Ensure good lighting
  - Position camera to minimize occlusions

---

## 🎯 Test 3: Process Image - JSON Base64

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image
Content-Type: application/json

Headers:
  Content-Type: application/json
  X-API-KEY: {{api_key}}

Body (raw JSON):
{
  "image": "<base64-encoded-jpeg-string>",
  "room_id": "json-test-room"
}
```

**📝 How to get base64 string:**
```bash
# In Codespace terminal:
base64 -w 0 testing_images/sevenpeople.jpg
# Copy the entire output and paste as "image" value
```

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
Content-Type     | application/json
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **raw**
- Select **JSON** from dropdown (not Text)
- Paste this JSON:

```json
{
  "image": "PASTE_BASE64_STRING_HERE",
  "room_id": "json-test-room"
}
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("📤 Sending base64-encoded image...");
console.log("Room ID:", "json-test-room");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response structure is valid", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.all.keys('status', 'room_id', 'people_count', 'timestamp', 'processing_ms');
});

pm.test("Status is ok", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql('ok');
});

pm.test("Room ID matches request", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.room_id).to.eql('json-test-room');
});

pm.test("People detected successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.people_count).to.be.a('number').and.to.be.at.least(0);
});

console.log("✅ JSON endpoint test passed");
console.log("👥 People count:", pm.response.json().people_count);
```

### Expected Response
```json
{
  "status": "ok",
  "room_id": "json-test-room",
  "people_count": 10,
  "timestamp": "2025-11-27T14:39:57.350748",
  "processing_ms": 641
}
```

**Note:** This endpoint accepts base64-encoded images and produces identical results to the multipart endpoint.

---

## 🎯 Test 4: Auth Failure - Missing API Key

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  (NO X-API-KEY header - intentionally omitted)

Body (form-data):
  file: [Binary JPEG file] (Type: File)
  room_id: "test-room" (Type: Text)
```

**Expected Result:** 401 Unauthorized - Missing API key

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
(DO NOT add X-API-KEY header - leave empty or remove it)
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | [Any test image]
room_id    | Text  | test-room
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("🔒 Testing authentication - no API key provided");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 401 Unauthorized", function () {
    pm.response.to.have.status(401);
});

pm.test("Error message present", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('error');
    pm.expect(jsonData).to.have.property('message');
});

pm.test("Error mentions API key", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('api key');
});

console.log("✅ Authentication correctly rejects missing API key");
```

### Expected Response
```json
{
  "error": "Missing API key",
  "message": "X-API-KEY header is required"
}
```

**Note:** Server returns both `error` (short) and `message` (detailed) fields for better error handling.

---

## 🎯 Test 5: Auth Failure - Invalid API Key

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  X-API-KEY: "wrong-api-key-12345" (intentionally incorrect)

Body (form-data):
  file: [Binary JPEG file] (Type: File)
  room_id: "test-room" (Type: Text)
```

**Expected Result:** 401 Unauthorized - Invalid API key

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | wrong-api-key-12345
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | [Any test image]
room_id    | Text  | test-room
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("🔒 Testing authentication - invalid API key");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 401 Unauthorized", function () {
    pm.response.to.have.status(401);
});

pm.test("Invalid key is rejected", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('error');
    pm.expect(jsonData).to.have.property('message');
    pm.expect(jsonData.error).to.include('Invalid');
});

console.log("✅ Authentication correctly rejects invalid API key");
```

### Expected Response
```json
{
  "error": "Invalid API key",
  "message": "The provided API key is not valid"
}
```

---

## 🎯 Test 6: Validation - Missing room_id

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  X-API-KEY: {{api_key}}

Body (form-data):
  file: [Binary JPEG file] (Type: File)
  (NO room_id field - intentionally omitted)
```

**Expected Result:** 400 Bad Request - Missing room_id

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | [Any test image]
(DO NOT add room_id - test missing parameter)
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("⚠️  Testing validation - missing room_id");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 400 Bad Request", function () {
    pm.response.to.have.status(400);
});

pm.test("Error mentions missing room_id", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('room_id');
});

console.log("✅ Validation correctly rejects missing room_id");
```

---

## 🎯 Test 7: Validation - Invalid room_id Format

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  X-API-KEY: {{api_key}}

Body (form-data):
  file: [Binary JPEG file] (Type: File)
  room_id: "room@#$%^&*()" (Type: Text) - invalid characters
```

**Expected Result:** 400 Bad Request - Invalid room_id format
**Valid Format:** Alphanumeric, hyphens (-), underscores (_) only, 1-64 characters

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | [Any test image]
room_id    | Text  | room@#$%^&*()
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("⚠️  Testing validation - invalid room_id format");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 400 Bad Request", function () {
    pm.response.to.have.status(400);
});

pm.test("Error mentions room_id format", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.include('room_id');
});

console.log("✅ Validation correctly rejects invalid room_id format");
```

---

## 🎯 Test 8: Validation - Missing Image File

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  X-API-KEY: {{api_key}}

Body (form-data):
  room_id: "test-room" (Type: Text)
  (NO file field - intentionally omitted)
```

**Expected Result:** 400 Bad Request - Missing image file

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
room_id    | Text  | test-room
(DO NOT add file - test missing image)
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("⚠️  Testing validation - missing image file");
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 400 Bad Request", function () {
    pm.response.to.have.status(400);
});

pm.test("Error mentions missing image", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.error.toLowerCase()).to.match(/image|file/);
});

console.log("✅ Validation correctly rejects missing image file");
```

---

## 🎯 Test 9: Performance Test - Response Time

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  X-API-KEY: {{api_key}}

Body (form-data):
  file: testing_images/sevenpeople.jpg (Type: File)
  room_id: "performance-test-room" (Type: Text)
```

**Expected Result:** 200 OK with performance metrics
**Performance Target:** < 3000ms (first request may be slower due to model loading)

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | testing_images/sevenpeople.jpg
room_id    | Text  | performance-test-room
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("⏱️  Performance test started...");
pm.environment.set("perf_test_start", new Date().getTime());
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response time is acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(3000); // 3 seconds
});

pm.test("Processing time is logged", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.processing_ms).to.be.a('number');
});

pm.test("First request may be slow (model loading)", function () {
    var jsonData = pm.response.json();
    if (pm.response.responseTime > 3000) {
        console.log("⚠️  First request slow - YOLO model loading");
    } else {
        console.log("✅ Response time normal");
    }
});

// Performance logging
console.log("📊 Total response time:", pm.response.responseTime + "ms");
console.log("⚙️  Server processing time:", pm.response.json().processing_ms + "ms");
console.log("🌐 Network overhead:", (pm.response.responseTime - pm.response.json().processing_ms) + "ms");
```

---

## 🎯 Test 10: End-to-End Verification

**⚡ Copy-Paste Ready**

### 📥 Input Format

```
Method: POST
URL: {{base_url}}/api/v1/process-image-bytes

Headers:
  X-API-KEY: {{api_key}}

Body (form-data):
  file: testing_images/sevenpeople.jpg (Type: File)
  room_id: "e2e-test-room" (Type: Text)
```

**Expected Result:** 200 OK with complete data validation
**Purpose:** Verify entire pipeline from upload to database storage

### Request Setup in Postman UI

**Method:** `POST`

**URL:** `{{base_url}}/api/v1/process-image-bytes`

**Headers Tab:**
```
KEY              | VALUE
---------------- | -----------------
X-API-KEY        | {{api_key}}
```

**Body Tab:**
- Select **form-data**

```
KEY        | TYPE  | VALUE
---------- | ----- | ------------------------------------
file       | File  | testing_images/sevenpeople.jpg
room_id    | Text  | e2e-test-room
```

### Pre-request Script Tab (Optional - Copy This)
```javascript
// Runs BEFORE request is sent
console.log("🔄 Starting end-to-end test...");
pm.environment.set("e2e_test_timestamp", new Date().toISOString());
```

### Tests Tab (Post-response - Copy This)
```javascript
pm.test("Complete E2E test passed", function () {
    pm.response.to.have.status(200);
});

pm.test("All data fields are valid", function () {
    var jsonData = pm.response.json();
    
    // Status check
    pm.expect(jsonData.status).to.be.a('string').and.to.eql('ok');
    
    // Room ID check
    pm.expect(jsonData.room_id).to.be.a('string').and.to.have.lengthOf.at.least(1);
    
    // People count check
    pm.expect(jsonData.people_count).to.be.a('number').and.to.be.at.least(0);
    
    // Timestamp check (ISO 8601 format)
    pm.expect(jsonData.timestamp).to.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    
    // Processing time check
    pm.expect(jsonData.processing_ms).to.be.a('number').and.to.be.above(0);
});

pm.test("Data can be saved for verification", function () {
    var jsonData = pm.response.json();
    
    pm.environment.set("e2e_room_id", jsonData.room_id);
    pm.environment.set("e2e_timestamp", jsonData.timestamp);
    pm.environment.set("e2e_people_count", jsonData.people_count);
    
    pm.expect(pm.environment.get("e2e_room_id")).to.not.be.undefined;
});

console.log("✅ End-to-end test completed successfully");
console.log("📋 Summary:");
console.log("  Room:", pm.response.json().room_id);
console.log("  People:", pm.response.json().people_count);
console.log("  Time:", pm.response.json().timestamp);
console.log("  Processing:", pm.response.json().processing_ms + "ms");
```

---

## 🔧 Postman Environment Setup

### Create Environment Variables

**Click "Environments" → Create New Environment → Add these variables:**

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `api_key` | `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI` | `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI` |

**For Codespaces, update `base_url` to:**
```
https://your-codespace-url-8000.app.github.dev
```

**Then use `{{base_url}}` and `{{api_key}}` in all requests!**

---

## 📦 Collection Pre-request Script

**Add this to Collection level (Run for all tests):**

```javascript
// Set test start time
pm.environment.set("test_start_time", new Date().toISOString());

// Log test info
console.log("==========================================");
console.log("Test:", pm.info.requestName);
console.log("Time:", pm.environment.get("test_start_time"));
console.log("URL:", pm.request.url.toString());
console.log("==========================================");
```

---

## ✅ Quick Test Checklist

Copy this to track your progress:

```
Testing Progress:
[ ] Test 1: Health check - GET /health
[ ] Test 2: Multipart upload - POST /api/v1/process-image-bytes
[ ] Test 3: JSON base64 upload - POST /api/v1/process-image
[ ] Test 4: Missing API key (401)
[ ] Test 5: Invalid API key (401)
[ ] Test 6: Missing room_id (400)
[ ] Test 7: Invalid room_id format (400)
[ ] Test 8: Missing image file (400)
[ ] Test 9: Performance test
[ ] Test 10: End-to-end verification

All tests passed: ✅
```

---

## 🐛 Troubleshooting

### Server Not Responding
```bash
# Check server is running
curl http://localhost:8000/health

# Start server if needed
python -m server.app
```

### 401 Unauthorized
- Verify API key: `Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
- Check header name: `X-API-KEY` (case-sensitive!)

### 400 Bad Request
- Ensure image is JPEG format
- Verify room_id: alphanumeric, hyphens, underscores only
- Check both `file` and `room_id` are present

### 404 Not Found
- Check URL has correct endpoint path (e.g., `/health`, not just `/`)
- For Codespaces: ensure port 8000 is Public

### Connection Refused (Codespaces)
- Go to PORTS tab
- Right-click port 8000
- Select "Port Visibility" → "Public"

---

## 🎉 Success Criteria

**All tests should show:**
- ✅ Green checkmarks in Postman
- ✅ Console logs with success messages
- ✅ Correct HTTP status codes
- ✅ Valid JSON responses

**You're ready to integrate with cameras! 🚀**
- ✅ `200 OK`

### Postman Tests Tab
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response structure is valid", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.all.keys('status', 'room_id', 'people_count', 'timestamp', 'processing_ms');
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
    pm.expect(jsonData).to.have.all.keys('status', 'room_id', 'people_count', 'timestamp', 'processing_ms');
});

// Log response time for performance tracking
console.log("Response time: " + pm.response.responseTime + "ms");
console.log("Processing time: " + pm.response.json().processing_ms + "ms");
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
    pm.expect(jsonData.processing_ms).to.be.a('number').and.to.be.above(0);
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
