#!/usr/bin/env python3
"""
Test script to verify Supabase connection and configuration.
"""

import sys
from backend.utils.env_utils import load_and_validate_env, EnvironmentValidationError
from backend.utils.supabase_utils import create_supabase_client, SupabaseConnectionError

def test_environment():
    """Test environment variable validation."""
    print("=" * 60)
    print("Testing Environment Configuration")
    print("=" * 60)
    
    try:
        config = load_and_validate_env()
        print("✓ Environment variables loaded and validated")
        print(f"  - Supabase URL: {config['SUPABASE_URL']}")
        print(f"  - Table Name: {config.get('TABLE_NAME', 'detections')}")
        print(f"  - Model Path: {config.get('YOLO_MODEL_PATH', 'yolov8n.pt')}")
        return config
    except EnvironmentValidationError as e:
        print(f"✗ Environment validation failed:")
        print(f"  {str(e)}")
        return None

def test_supabase_connection(config):
    """Test Supabase connection."""
    print("\n" + "=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    try:
        client = create_supabase_client(
            config['SUPABASE_URL'],
            config['SUPABASE_SERVICE_KEY']
        )
        print("✓ Supabase client created successfully")
        
        # Try to query the table
        table_name = config.get('TABLE_NAME', 'detections')
        print(f"\nTesting table access: {table_name}")
        
        response = client.table(table_name).select("*").limit(1).execute()
        print(f"✓ Successfully queried '{table_name}' table")
        print(f"  - Records found: {len(response.data)}")
        
        if response.data:
            print(f"  - Sample record: {response.data[0]}")
        
        return True
    except SupabaseConnectionError as e:
        print(f"✗ Supabase connection failed:")
        print(f"  {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error:")
        print(f"  {str(e)}")
        return False

def test_table_structure(config):
    """Test that the table has the expected structure."""
    print("\n" + "=" * 60)
    print("Verifying Table Structure")
    print("=" * 60)
    
    try:
        client = create_supabase_client(
            config['SUPABASE_URL'],
            config['SUPABASE_SERVICE_KEY']
        )
        
        table_name = config.get('TABLE_NAME', 'detections')
        
        # Try to select with expected columns
        response = client.table(table_name).select(
            "id, room_id, person_count, timestamp"
        ).limit(1).execute()
        
        print(f"✓ Table '{table_name}' has correct structure")
        print("  Expected columns:")
        print("    - id (UUID)")
        print("    - room_id (TEXT)")
        print("    - person_count (INTEGER)")
        print("    - timestamp (TIMESTAMPTZ)")
        
        return True
    except Exception as e:
        print(f"✗ Table structure verification failed:")
        print(f"  {str(e)}")
        print("\nMake sure you've run the SQL setup script in Supabase!")
        return False

def main():
    """Run all tests."""
    print("\n🔍 Supabase Configuration Test\n")
    
    # Test 1: Environment
    config = test_environment()
    if not config:
        print("\n❌ Setup incomplete: Fix environment configuration first")
        sys.exit(1)
    
    # Test 2: Connection
    if not test_supabase_connection(config):
        print("\n❌ Setup incomplete: Cannot connect to Supabase")
        sys.exit(1)
    
    # Test 3: Table Structure
    if not test_table_structure(config):
        print("\n❌ Setup incomplete: Table structure incorrect")
        sys.exit(1)
    
    # All tests passed
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour Supabase setup is complete and working correctly.")
    print("You can now run the image processing pipeline.")
    print("\nNext steps:")
    print("  1. Test with a sample image:")
    print("     python -m backend.process_images '<base64-image>' 'test_room'")
    print("  2. Check data in Supabase dashboard")
    print("  3. Integrate with your camera system")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
