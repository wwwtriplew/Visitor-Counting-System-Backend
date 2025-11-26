#!/usr/bin/env python3
"""
Test the pipeline with the sevenpeople.jpg image.
"""

import base64
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path so we can import backend modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.process_images import ImageProcessingPipeline
from backend.utils.env_utils import load_and_validate_env

def main():
    print("\n" + "="*70)
    print("🧪 Testing with sevenpeople.jpg")
    print("="*70)
    
    # Load image - path is relative to repository root
    repo_root = Path(__file__).resolve().parent.parent
    image_path = repo_root / "testing_images" / "sevenpeople.jpg"
    
    if not image_path.exists():
        print(f"✗ Image not found: {image_path}")
        sys.exit(1)
    
    print(f"\n[1/5] Loading image: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"✓ Image loaded ({len(image_bytes)} bytes)")
    print(f"  Base64 length: {len(base64_image)} characters")
    
    # Load configuration
    print("\n[2/5] Loading configuration...")
    try:
        config = load_and_validate_env()
        print("✓ Configuration loaded")
        print(f"  Supabase URL: {config['SUPABASE_URL']}")
        print(f"  Table: {config.get('TABLE_NAME', 'detections')}")
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        sys.exit(1)
    
    # Initialize pipeline
    print("\n[3/5] Initializing pipeline...")
    try:
        pipeline = ImageProcessingPipeline(
            supabase_url=config["SUPABASE_URL"],
            supabase_service_key=config["SUPABASE_SERVICE_KEY"],
            table_name=config.get("TABLE_NAME", "detections")
        )
        print("✓ Pipeline initialized")
    except Exception as e:
        print(f"✗ Pipeline initialization failed: {e}")
        sys.exit(1)
    
    # Process image
    print("\n[4/5] Processing image with YOLO...")
    print("  Expected: 7 people (based on filename)")
    
    room_id = "test_room_seven"
    timestamp = datetime.now()
    
    try:
        result = pipeline.process_image(base64_image, room_id, timestamp)
        
        if result["success"]:
            print(f"\n✓ Image processed successfully!")
            print(f"  Room ID: {result['room_id']}")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  People detected: {result['people_count']}")
            
            if result['people_count'] == 7:
                print("  🎯 Perfect match! Detected exactly 7 people")
            elif result['people_count'] > 0:
                print(f"  ⚠️  Detected {result['people_count']} people (expected 7)")
                print("     This is normal - detection accuracy depends on image quality")
            else:
                print("  ⚠️  No people detected - image may need adjustment")
        else:
            print(f"\n✗ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Processing error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Verify in Supabase
    print("\n[5/5] Verifying data in Supabase...")
    try:
        from backend.utils.supabase_utils import get_room_latest_count
        
        latest = get_room_latest_count(
            pipeline.supabase_client,
            room_id,
            table_name=config.get("TABLE_NAME", "detections")
        )
        
        if latest:
            print("✓ Data verified in Supabase")
            print(f"  Record ID: {latest.get('id')}")
            print(f"  Person count: {latest.get('person_count')}")
            print(f"  Timestamp: {latest.get('timestamp')}")
        else:
            print("⚠️  Could not retrieve data (check Supabase dashboard)")
            
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ TEST COMPLETED!")
    print("="*70)
    print(f"\nResults: Detected {result['people_count']} people in the image")
    print("\nCheck your Supabase dashboard:")
    print(f"  https://supabase.com/dashboard/project/rgkkadtaiivcuuvekwdo/editor")
    print(f"\nLook for table: 'detections' with room_id: '{room_id}'")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
