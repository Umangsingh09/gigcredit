from supabase import Client, create_client
from backend.app.core.config import SUPABASE_KEY, SUPABASE_URL

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None