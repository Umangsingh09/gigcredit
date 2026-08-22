import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_KEY)

# Defaults to "production" when unset so an operator's omission fails
# closed (strict auth) rather than open. Only an explicit
# ENVIRONMENT=development opts into any development-only behavior
# (see backend/app/api/deps.py's local-auth fallback).
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
IS_DEVELOPMENT = ENVIRONMENT == "development"
