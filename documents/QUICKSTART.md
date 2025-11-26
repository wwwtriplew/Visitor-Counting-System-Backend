# Quick Start Guide - Visitor Counting System Backend

## 5-Minute Setup

### 1. Prerequisites
```bash
# Check Python version (3.8+ required)
python --version

# Check pip
pip --version
```

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/wwwtriplew/Visitor-Counting-System-Backend.git
cd Visitor-Counting-System-Backend

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Supabase
1. Go to https://supabase.com and create a free account
2. Create a new project
3. Navigate to Settings → API
4. Copy your **Project URL** and **service_role key** (not anon key!)

### 4. Set Up Database
In Supabase SQL Editor, run:
```sql
CREATE TABLE room_stats (
  id BIGSERIAL PRIMARY KEY,
  room_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  people_count INT NOT NULL,
  CONSTRAINT people_count_non_negative CHECK (people_count >= 0)
);

-- Add indexes for performance
CREATE INDEX idx_room_stats_room_id ON room_stats(room_id);
CREATE INDEX idx_room_stats_timestamp ON room_stats(timestamp DESC);
```

### 5. Configure Environment
```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

Add your Supabase credentials:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### 6. Test the System
```bash
# Create a test image (or use your own)
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" > test_image.txt

# Run the processor
python -m backend.process_images "$(cat test_image.txt)" "test_room"
```

Expected output:
```
2025-11-25 14:30:00 - backend.utils.env_utils - INFO - Validating environment configuration...
2025-11-25 14:30:01 - backend.process_images - INFO - Initializing Image Processing Pipeline...
2025-11-25 14:30:02 - backend.process_images - INFO - YOLO model loaded
2025-11-25 14:30:02 - backend.process_images - INFO - Processing image for room 'test_room'...
2025-11-25 14:30:03 - backend.process_images - INFO - Successfully processed image

✓ Successfully processed image for room 'test_room'
  Timestamp: 2025-11-25T14:30:03.123456
  People count: 0
```

## Common First-Time Issues

### Issue: "SUPABASE_URL is not set"
**Solution**: Make sure .env file exists and contains valid credentials

### Issue: "Failed to load YOLO model"
**Solution**: First run requires internet to download the model (~6MB). Wait for download to complete.

### Issue: "Module 'backend' not found"
**Solution**: Run from project root directory, use `python -m backend.process_images`

## Next Steps

### For Production Use
1. Read the full [README_NEW.md](README_NEW.md)
2. Review [IMPROVEMENTS.md](IMPROVEMENTS.md) for details
3. Set up monitoring and logging
4. Configure backup strategy

### For Development
1. Create a separate `.env` file for development
2. Use the `ImageProcessingPipeline` class for efficiency
3. Enable DEBUG logging: `logging.basicConfig(level=logging.DEBUG)`
4. Review the code documentation in each module

## Example Integration

```python
# example_usage.py
from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env
import time

# Initialize once
config = load_and_validate_env()
pipeline = ImageProcessingPipeline(
    supabase_url=config["SUPABASE_URL"],
    supabase_service_key=config["SUPABASE_SERVICE_KEY"]
)

# Simulate processing images every minute
while True:
    # Get image from camera (replace with actual camera code)
    base64_image = get_camera_image("camera_1")
    
    # Process and store
    result = pipeline.process_image(base64_image, "lobby")
    
    if result["success"]:
        print(f"✓ Lobby: {result['people_count']} people")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Wait 1 minute
    time.sleep(60)
```

## Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Supabase project created
- [ ] Database table created
- [ ] .env file configured
- [ ] Test run successful
- [ ] Can see data in Supabase dashboard

## Support

If you encounter issues:
1. Check the [Troubleshooting section in README_NEW.md](README_NEW.md#troubleshooting)
2. Review [IMPROVEMENTS.md](IMPROVEMENTS.md) for system details
3. Enable DEBUG logging to see detailed information
4. Create an issue on GitHub with error logs

## Quick Reference

### File Structure
```
backend/
├── config.py              # Configuration constants
├── process_images.py      # Main script (use this!)
└── utils/
    ├── env_utils.py       # Environment validation
    ├── image_utils.py     # Image processing
    ├── yolo_utils.py      # YOLO inference
    └── supabase_utils.py  # Database operations
```

### Key Commands
```bash
# Process single image
python -m backend.process_images "<base64>" "room_id"

# Process with timestamp
python -m backend.process_images "<base64>" "room_id" "2025-11-25T14:30:00"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Test imports
python -c "from backend.utils.env_utils import load_and_validate_env; print('OK')"
```

### Environment Variables
```bash
# Required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx...

# Optional (with defaults)
YOLO_MODEL_PATH=yolov8n.pt
TABLE_NAME=room_stats
```

---

**Ready to go!** 🚀 Your visitor counting system is now set up and ready for production use.
