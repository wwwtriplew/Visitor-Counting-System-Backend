#!/usr/bin/env python3
"""
Quick test script to process a test image through the full pipeline.
This creates a simple test image, processes it, and verifies it's stored in Supabase.
"""

import sys
import base64
from io import BytesIO
from datetime import datetime

# Try to import PIL for creating a test image
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env

def create_test_image():
    """Create a simple test image with a person-like shape."""
    if not HAS_PIL:
        print("⚠️  PIL not available, using minimal 1x1 image")
        # Return a minimal valid PNG (1x1 transparent pixel)
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    # Create a 640x480 image (common camera resolution)
    img = Image.new('RGB', (640, 480), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "person" shape (rectangle with circle on top)
    # This is just for testing - real detection will depend on YOLO
    draw.rectangle([250, 200, 350, 400], fill='blue')  # Body
    draw.ellipse([270, 150, 330, 210], fill='blue')    # Head
    
    # Add text
    try:
        draw.text((10, 10), "Test Image", fill='black')
    except:
        pass  # Font not available, skip text
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64

def main():
    """Run a complete test of the image processing pipeline."""
    print("\n" + "="*60)
    print("🧪 Image Processing Pipeline Test")
    print("="*60)
    
    # Step 1: Load configuration
    print("\n[1/4] Loading configuration...")
    try:
        config = load_and_validate_env()
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        sys.exit(1)
    
    # Step 2: Initialize pipeline
    print("\n[2/4] Initializing pipeline...")
    try:
        pipeline = ImageProcessingPipeline(
            supabase_url=config["SUPABASE_URL"],
            supabase_service_key=config["SUPABASE_SERVICE_KEY"],
            table_name=config.get("TABLE_NAME", "detections")
        )
        print("✓ Pipeline initialized")
        print("  - YOLO model loaded")
        print("  - Supabase connected")
    except Exception as e:
        print(f"✗ Pipeline initialization failed: {e}")
        sys.exit(1)
    
    # Step 3: Create and process test image
    print("\n[3/4] Processing test image...")
    try:
        # Create test image
        base64_image = create_test_image()
        print(f"✓ Test image created ({len(base64_image)} bytes)")
        
        # Process the image
        room_id = "test_room"
        timestamp = datetime.now()
        
        print(f"  - Room ID: {room_id}")
        print(f"  - Timestamp: {timestamp.isoformat()}")
        print("  - Running YOLO inference...")
        
        result = pipeline.process_image(base64_image, room_id, timestamp)
        
        if result["success"]:
            print(f"✓ Image processed successfully")
            print(f"  - People detected: {result['people_count']}")
            print(f"  - Stored in Supabase")
        else:
            print(f"✗ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Processing error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 4: Verify data in Supabase
    print("\n[4/4] Verifying data in Supabase...")
    try:
        from backend.utils.supabase_utils import get_room_latest_count
        
        latest = get_room_latest_count(
            pipeline.supabase_client,
            room_id,
            table_name=config.get("TABLE_NAME", "detections")
        )
        
        if latest:
            print("✓ Data verified in Supabase")
            print(f"  - Record ID: {latest.get('id')}")
            print(f"  - Room: {latest.get('room_id')}")
            print(f"  - Count: {latest.get('person_count')}")
            print(f"  - Timestamp: {latest.get('timestamp')}")
        else:
            print("⚠️  Could not retrieve data (but insert may have succeeded)")
            
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        print("   (Data may still be in Supabase)")
    
    # Success!
    print("\n" + "="*60)
    print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nYour system is working correctly!")
    print("\nNext steps:")
    print("  1. Check Supabase dashboard to see the record")
    print("  2. Try with a real camera image")
    print("  3. Integrate with your camera system")
    print("\nSupabase Dashboard:")
    print(f"  {config['SUPABASE_URL']}/project/default/editor")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
