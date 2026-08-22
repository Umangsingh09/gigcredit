"""deps

Shared FastAPI dependencies for authenticated routes.
"""

from fastapi import Header, HTTPException

from backend.app.core.supabase import supabase


def get_current_user_id(authorization: str = Header(None)) -> str:
    """Resolve the authenticated Supabase user id from a Bearer token.

    Verification is delegated to Supabase Auth itself
    (supabase.auth.get_user) rather than decoding the JWT locally, so
    this stays correct regardless of which signing key/algorithm
    Supabase issues tokens with, and never requires the service-role key
    or any signing secret to live in backend code.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

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
