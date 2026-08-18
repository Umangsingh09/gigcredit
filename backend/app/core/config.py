import os
from pathlib import Path

from dotenv import load_dotenv


# Find the backend/.env file
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not configured")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is not configured")