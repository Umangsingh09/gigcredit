"""deps

Shared FastAPI dependencies for authenticated routes.
"""

from fastapi import Header, HTTPException

from backend.app.core.config import ENVIRONMENT
from backend.app.core.supabase import supabase


_LOCAL_TOKEN_PREFIX = "local-"
_DEVELOPMENT_ENVIRONMENT = "development"


def get_current_user_id(authorization: str = Header(None)) -> str:
    """Resolve the authenticated Supabase user id from a Bearer token.

    Verification is delegated to Supabase Auth itself
    (supabase.auth.get_user) rather than decoding the JWT locally, so
    this stays correct regardless of which signing key/algorithm
    Supabase issues tokens with, and never requires the service-role key
    or any signing secret to live in backend code.

    Local-dev fallback: this function accepts a "local-<email>" token
    ONLY when BOTH of the following are true:
      1. No Supabase project is configured at all (`supabase` is None
         — see backend/app/core/supabase.py, SUPABASE_ENABLED).
      2. ENVIRONMENT is explicitly set to "development" (see
         backend/app/core/config.py). ENVIRONMENT defaults to
         "production" when unset, so this is fail-closed by default:
         an operator who forgets to set Supabase credentials in
         production gets 401 on every request, not silent
         impersonation. "supabase is None" alone is NOT a reliable
         signal that this is a trusted local environment — it can also
         mean a real deployment is missing its Supabase configuration
         or hit a transient connection failure at startup, so a
         second, independent, explicit opt-in is required.

    That "local-<email>" shape is exactly what /auth/register and
    /auth/login themselves issue in no-Supabase + development mode, and
    no other token value is ever accepted there. The moment real
    Supabase credentials are configured, `supabase` is no longer None
    and this whole branch is unreachable regardless of ENVIRONMENT —
    every request is verified against Supabase Auth, with no bypass of
    any kind. This must never be widened to accept arbitrary tokens, to
    run when `supabase` is configured, or to run without the explicit
    ENVIRONMENT=development check.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    if supabase is None:
        if (
            ENVIRONMENT == _DEVELOPMENT_ENVIRONMENT
            and token.startswith(_LOCAL_TOKEN_PREFIX)
            and len(token) > len(_LOCAL_TOKEN_PREFIX)
        ):
            return token[len(_LOCAL_TOKEN_PREFIX):]
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = getattr(response, "user", None) or (
        response.get("user") if isinstance(response, dict) else None
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = getattr(user, "id", None) or user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return str(user_id)
