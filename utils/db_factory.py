"""Database factory - returns appropriate database client based on config."""
from config import Config


def get_database():
    """Get database client based on configuration."""
    if Config.DATABASE_TYPE == 'neon':
        from utils.neon_database import NeonDB
        return NeonDB()
    else:
        from utils.database import SupabaseDB
        return SupabaseDB()
