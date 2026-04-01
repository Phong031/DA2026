"""
Supabase client connection manager
"""
from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = False
    
    def initialize(self, url: str, key: str) -> None:
        """Initialize the Supabase client"""
        if not self.initialized:
            try:
                self._client = create_client(url, key)
                self.initialized = True
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize: {e}")
                raise
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance"""
        if not self.initialized or not self._client:
            raise RuntimeError("Supabase client not initialized")
        return self._client