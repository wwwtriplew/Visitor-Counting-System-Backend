from datetime import datetime

from supabase import create_client, Client


def create_supabase_client(url: str, service_role_key: str) -> Client:
    """
    Create a Supabase client using the service role key.

    Args:
        url: Supabase project URL.
        service_role_key: Supabase service role key.

    Returns:
        Supabase client instance.
    """
    client = create_client(url, service_role_key)
    return client


def insert_visitor_count(
    client: Client,
    room_id: str,
    timestamp: datetime,
    people_count: int,
    table_name: str = "visitor_counts"
) -> dict:
    """
    Insert a visitor count record into Supabase.

    Args:
        client: Supabase client instance.
        room_id: Identifier for the room.
        timestamp: Timestamp of the count.
        people_count: Number of people detected.
        table_name: Name of the Supabase table.

    Returns:
        Response from Supabase insert operation.
    """
    data = {
        "room_id": room_id,
        "timestamp": timestamp.isoformat(),
        "people_count": people_count
    }

    response = client.table(table_name).insert(data).execute()
    return response.data
