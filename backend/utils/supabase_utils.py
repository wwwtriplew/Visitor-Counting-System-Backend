"""
Supabase integration utilities for the Visitor Counting System Backend.

This module provides robust functions for interacting with Supabase,
including connection management, data insertion with retry logic, and
comprehensive error handling for network failures and invalid data.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, cast

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from backend.config import (
    DEFAULT_TABLE_NAME,
    MAX_RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
    CONNECTION_TIMEOUT,
    VALID_ROOM_ID_PATTERN,
    MIN_PEOPLE_COUNT,
    MAX_PEOPLE_COUNT
)


# Configure logging
logger = logging.getLogger(__name__)


class SupabaseError(Exception):
    """Base exception for Supabase-related errors."""
    pass


class SupabaseConnectionError(SupabaseError):
    """Raised when connection to Supabase fails."""
    pass


class SupabaseValidationError(SupabaseError):
    """Raised when data validation fails before insertion."""
    pass


class SupabaseInsertError(SupabaseError):
    """Raised when data insertion fails."""
    pass


def validate_room_id(room_id: str) -> None:
    """
    Validate that a room ID meets the expected format.
    
    Args:
        room_id: The room identifier to validate.
        
    Raises:
        SupabaseValidationError: If the room ID is invalid.
    """
    if not room_id or not isinstance(room_id, str):
        raise SupabaseValidationError("Room ID must be a non-empty string")
    
    if not re.match(VALID_ROOM_ID_PATTERN, room_id):
        raise SupabaseValidationError(
            f"Invalid room ID format: '{room_id}'. "
            f"Must match pattern: {VALID_ROOM_ID_PATTERN}"
        )
    
    if len(room_id) > 50:
        raise SupabaseValidationError(
            f"Room ID too long: {len(room_id)} characters (maximum 50)"
        )


def validate_people_count(people_count: int) -> None:
    """
    Validate that a people count is within acceptable bounds.
    
    Args:
        people_count: The number of people detected.
        
    Raises:
        SupabaseValidationError: If the count is invalid.
    """
    if not isinstance(people_count, int):
        raise SupabaseValidationError(
            f"People count must be an integer, got {type(people_count)}"
        )
    
    if people_count < MIN_PEOPLE_COUNT:
        raise SupabaseValidationError(
            f"People count ({people_count}) cannot be negative"
        )
    
    if people_count > MAX_PEOPLE_COUNT:
        raise SupabaseValidationError(
            f"People count ({people_count}) exceeds maximum allowed ({MAX_PEOPLE_COUNT})"
        )


def validate_timestamp(timestamp: datetime) -> None:
    """
    Validate that a timestamp is reasonable.
    
    Args:
        timestamp: The timestamp to validate.
        
    Raises:
        SupabaseValidationError: If the timestamp is invalid.
    """
    from datetime import timedelta, timezone
    
    if not isinstance(timestamp, datetime):
        raise SupabaseValidationError(
            f"Timestamp must be a datetime object, got {type(timestamp)}"
        )
    
    # Check if timestamp is not in the future (with 1 minute tolerance)
    # Handle both timezone-aware and timezone-naive datetimes
    if timestamp.tzinfo is not None:
        # Timestamp is timezone-aware, use UTC now
        now = datetime.now(timezone.utc)
    else:
        # Timestamp is timezone-naive, use naive now
        now = datetime.now()
    
    if timestamp > now.replace(microsecond=0).replace(second=0) + timedelta(minutes=1):
        raise SupabaseValidationError(
            f"Timestamp {timestamp.isoformat()} is in the future"
        )


def create_supabase_client(
    url: str, 
    service_role_key: str,
    timeout: Optional[int] = None
) -> Client:
    """
    Create a Supabase client using the service role key.
    
    This function establishes a connection to Supabase with the service
    role key, which bypasses Row Level Security (RLS) and is needed for
    backend operations.

    Args:
        url: Supabase project URL (e.g., https://xxx.supabase.co).
        service_role_key: Supabase service role key (JWT token).
        timeout: Connection timeout in seconds. If None, uses default.

    Returns:
        Configured Supabase client instance ready for database operations.
        
    Raises:
        SupabaseConnectionError: If client creation fails.
    """
    if not url or not isinstance(url, str):
        raise SupabaseConnectionError("Supabase URL must be a non-empty string")
    
    if not service_role_key or not isinstance(service_role_key, str):
        raise SupabaseConnectionError("Service role key must be a non-empty string")
    
    try:
        logger.info(f"Creating Supabase client for URL: {url}")
        
        # Configure client options with timeout
        if timeout is None:
            timeout = CONNECTION_TIMEOUT
        
        # Create the client with custom options
        client = create_client(url, service_role_key)
        
        if client is None:
            raise SupabaseConnectionError("Failed to create Supabase client")
        
        logger.info("Supabase client created successfully")
        return client
        
    except SupabaseConnectionError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise SupabaseConnectionError(
            f"Failed to create Supabase client: {str(e)}"
        )


def insert_visitor_count(
    client: Client,
    room_id: str,
    timestamp: datetime,
    people_count: int,
    table_name: Optional[str] = None,
    retry_attempts: Optional[int] = None,
    retry_delay: Optional[float] = None
) -> Dict[str, Any]:
    """
    Insert a visitor count record into Supabase with retry logic.
    
    This function validates the input data, attempts to insert it into
    Supabase, and retries on failure with exponential backoff. It provides
    robust error handling for network issues and invalid data.

    Args:
        client: Supabase client instance.
        room_id: Identifier for the room (e.g., "room_101", "lobby").
        timestamp: Timestamp when the count was taken.
        people_count: Number of people detected (must be >= 0).
        table_name: Name of the Supabase table. If None, uses default.
        retry_attempts: Maximum number of retry attempts. If None, uses default.
        retry_delay: Initial delay between retries in seconds. If None, uses default.

    Returns:
        Dictionary containing the inserted data with any server-generated fields.
        
    Raises:
        SupabaseValidationError: If input data validation fails.
        SupabaseInsertError: If insertion fails after all retry attempts.
    """
    # Use defaults if not specified
    if table_name is None:
        table_name = DEFAULT_TABLE_NAME
    if retry_attempts is None:
        retry_attempts = MAX_RETRY_ATTEMPTS
    if retry_delay is None:
        retry_delay = RETRY_DELAY_SECONDS
    
    # Validate all inputs before attempting insertion
    try:
        validate_room_id(room_id)
        validate_people_count(people_count)
        validate_timestamp(timestamp)
    except SupabaseValidationError as e:
        logger.error(f"Data validation failed: {str(e)}")
        raise
    
    # Prepare data for insertion
    data = {
        "room_id": room_id,
        "timestamp": timestamp.isoformat(),
        "person_count": people_count  # Note: Column name is person_count in DB
    }
    
    logger.debug(f"Attempting to insert data: {data}")
    
    # Retry loop with exponential backoff
    last_error = None
    current_delay = retry_delay
    
    for attempt in range(1, retry_attempts + 1):
        try:
            logger.debug(
                f"Insert attempt {attempt}/{retry_attempts} for room {room_id}"
            )
            
            # Attempt to insert data
            response = client.table(table_name).insert(data).execute()
            
            # Check if insertion was successful
            if not response.data:
                raise SupabaseInsertError("Insert returned empty response")
            
            logger.info(
                f"Successfully inserted visitor count for room {room_id}: "
                f"{people_count} people at {timestamp.isoformat()}"
            )
            
            # Type cast: response.data is known to be Dict[str, Any] after successful insert
            result = response.data[0] if isinstance(response.data, list) else response.data
            return cast(Dict[str, Any], result)
            
        except Exception as e:
            last_error = e
            error_msg = str(e)
            
            # Log the error
            logger.warning(
                f"Insert attempt {attempt}/{retry_attempts} failed: {error_msg}"
            )
            
            # If this was the last attempt, don't wait before raising
            if attempt == retry_attempts:
                break
            
            # Wait before retrying (exponential backoff)
            logger.debug(f"Waiting {current_delay:.1f}s before retry...")
            time.sleep(current_delay)
            current_delay *= 2  # Exponential backoff
    
    # All retry attempts failed
    error_message = (
        f"Failed to insert visitor count after {retry_attempts} attempts. "
        f"Last error: {str(last_error)}"
    )
    logger.error(error_message)
    raise SupabaseInsertError(error_message)


def get_latest_counts(
    client: Client,
    table_name: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch the most recent visitor counts from Supabase.
    
    This function is useful for retrieving the latest occupancy data,
    which can be used by the frontend or for validation purposes.
    
    Args:
        client: Supabase client instance.
        table_name: Name of the Supabase table. If None, uses default.
        limit: Maximum number of records to retrieve.
    
    Returns:
        List of dictionaries containing recent visitor count records.
        
    Raises:
        SupabaseError: If the query fails.
    """
    if table_name is None:
        table_name = DEFAULT_TABLE_NAME
    
    try:
        logger.debug(f"Fetching latest {limit} counts from {table_name}")
        
        response = client.table(table_name)\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(limit)\
            .execute()
        
        logger.info(f"Retrieved {len(response.data)} recent counts")
        # Type cast: response.data is a list of dicts from Supabase query
        return cast(List[Dict[str, Any]], response.data)
        
    except Exception as e:
        logger.error(f"Failed to fetch latest counts: {str(e)}")
        raise SupabaseError(f"Failed to fetch data: {str(e)}")


def get_room_latest_count(
    client: Client,
    room_id: str,
    table_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent visitor count for a specific room.
    
    Args:
        client: Supabase client instance.
        room_id: Identifier for the room.
        table_name: Name of the Supabase table. If None, uses default.
    
    Returns:
        Dictionary with the latest count data, or None if no data exists.
        
    Raises:
        SupabaseError: If the query fails.
    """
    if table_name is None:
        table_name = DEFAULT_TABLE_NAME
    
    try:
        validate_room_id(room_id)
        
        logger.debug(f"Fetching latest count for room {room_id}")
        
        response = client.table(table_name)\
            .select("*")\
            .eq("room_id", room_id)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Retrieved latest count for room {room_id}")
            # Type cast: response.data[0] is a dict from Supabase query
            return cast(Dict[str, Any], response.data[0])
        else:
            logger.info(f"No data found for room {room_id}")
            return None
        
    except SupabaseValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch room data: {str(e)}")
        raise SupabaseError(f"Failed to fetch room data: {str(e)}")
