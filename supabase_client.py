import os
from supabase import create_client, Client
from dotenv import load_dotenv

class SupabaseClient:
    _instance = None

    @staticmethod
    def get_client():
        """Static access method."""
        if SupabaseClient._instance is None:
            SupabaseClient()
        return SupabaseClient._instance

    def __init__(self):
        """Virtually private constructor."""
        if SupabaseClient._instance is not None:
            raise Exception("This class is a singleton! Use get_client() to get the instance.")
        else:
            load_dotenv() # Load environment variables from .env file
            
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Use service role for backend operations
            
            if not url or not key:
                raise ValueError("Supabase URL and Service Role Key must be set in environment variables.")
            
            self.client: Client = create_client(url, key)
            SupabaseClient._instance = self.client
