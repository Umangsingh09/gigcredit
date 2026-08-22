from supabase import Client, create_client

from backend.app.core.config import SUPABASE_ENABLED, SUPABASE_KEY, SUPABASE_URL


supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_ENABLED else None