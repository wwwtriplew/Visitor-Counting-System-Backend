# Supabase Setup Complete! 🎉

Your Supabase configuration has been set up successfully.

## What Was Configured

### ✅ Environment File Created
- **File**: `.env`
- **Supabase URL**: https://rgkkadtaiivcuuvekwdo.supabase.co
- **Service Key**: Configured (keep this secret!)
- **Table Name**: detections
- **Model**: yolov8n.pt (will download automatically on first use)

### ✅ Code Updated
- Default table changed from `room_stats` to `detections`
- Column name changed from `people_count` to `person_count`
- Configuration matches your SQL schema

## Verify Setup

Run the test script to verify everything is working:

```bash
python test_setup.py
```

This will check:
1. ✓ Environment variables are valid
2. ✓ Connection to Supabase works
3. ✓ Table structure is correct

## Test with Sample Image

Create a test image and process it:

```bash
# Option 1: Use a tiny test image (1x1 pixel)
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" > test.txt
python -m backend.process_images "$(cat test.txt)" "lobby"

# Option 2: Use your own image
python -m backend.process_images "$(base64 -w 0 your_image.jpg)" "room_101"
```

## Check Results in Supabase

1. Go to https://rgkkadtaiivcuuvekwdo.supabase.co
2. Navigate to **Table Editor** → **detections**
3. You should see your test record with:
   - `room_id`: "lobby" or "room_101"
   - `person_count`: Number of people detected
   - `timestamp`: When the image was processed

## Your Table Schema

```
detections
├── id (UUID, Primary Key)
├── room_id (TEXT)
├── person_count (INTEGER)
├── timestamp (TIMESTAMPTZ)
└── created_at (TIMESTAMPTZ)
```

## Front-End Integration

Your front-end should use the **anon key** (NOT the service role key):

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://rgkkadtaiivcuuvekwdo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJna2thZHRhaWl2Y3V1dmVrd2RvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM5NzYyOTUsImV4cCI6MjA3OTU1MjI5NX0.cTAGAOIT_rpnQGNMO9v-o1PIHwyoB3r8xSPaqVccFrI'
)

// Get latest detections
const { data } = await supabase
  .from('detections')
  .select('*')
  .order('timestamp', { ascending: false })
  .limit(10)

// Get latest for specific room
const { data: roomData } = await supabase
  .from('detections')
  .select('*')
  .eq('room_id', 'lobby')
  .order('timestamp', { ascending: false })
  .limit(1)
  .single()

// Real-time updates
supabase
  .channel('detections_changes')
  .on('postgres_changes', 
    { event: 'INSERT', schema: 'public', table: 'detections' },
    (payload) => console.log('New detection:', payload.new)
  )
  .subscribe()
```

## Production Usage

### Python API (Recommended)
```python
from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env

# Initialize once
config = load_and_validate_env()
pipeline = ImageProcessingPipeline(
    supabase_url=config["SUPABASE_URL"],
    supabase_service_key=config["SUPABASE_SERVICE_KEY"]
)

# Process images
for image_data, room_id in camera_feed:
    result = pipeline.process_image(image_data, room_id)
    if result["success"]:
        print(f"✓ {room_id}: {result['people_count']} people")
```

## Security Notes

⚠️ **Important Security Reminders:**

1. **Never commit `.env` to Git** (it's already in `.gitignore`)
2. **Service role key** is SECRET - only use on backend
3. **Anon key** is public - use on frontend (has RLS restrictions)
4. Your RLS policies allow:
   - Public read access (frontend can read)
   - Authenticated insert (backend can write)

## Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the project root
cd /workspaces/Visitor-Counting-System-Backend
python -m backend.process_images ...
```

### "Cannot connect to Supabase"
- Check your internet connection
- Verify the URL and keys in `.env`
- Check Supabase project status

### "Table not found"
- Make sure you ran the SQL script in Supabase SQL Editor
- Check the table name matches "detections"

## Next Steps

1. ✅ Run `python test_setup.py` to verify setup
2. ✅ Test with a sample image
3. ✅ Check data appears in Supabase dashboard
4. ✅ Integrate with your camera system
5. ✅ Build the front-end to display the data

## Support Files

- `README_NEW.md` - Full documentation
- `QUICKSTART.md` - Quick setup guide
- `IMPROVEMENTS.md` - Technical details
- `test_setup.py` - Configuration test script

---

**Your backend is ready to count visitors! 🚀**

Need help? Check the troubleshooting section or review the documentation files.
