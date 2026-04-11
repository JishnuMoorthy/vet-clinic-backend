"""Database connection and initialization"""
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client with the SERVICE ROLE key.
# The backend is a trusted server — it bypasses RLS and enforces
# multi-tenant isolation via explicit clinic_id filtering in every route.
# The anon key must never be used here.
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY,
)


async def init_db():
    """Initialize database connection and test connectivity"""
    try:
        # Test connection by querying a simple table
        response = supabase.table("clinics").select("*").limit(1).execute()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("📝 Make sure to run migrations in Supabase SQL editor")
        return False


def get_supabase() -> Client:
    """Get Supabase client instance"""
    return supabase
