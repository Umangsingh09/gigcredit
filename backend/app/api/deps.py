"""deps

Shared FastAPI dependencies for authenticated routes.
"""

from fastapi import Header, HTTPException
from backend.app.core.supabase import supabase


def get_current_user_id(authorization: str = Header(None)) -> str:
    """Resolve the authenticated user id from a Bearer token or return default worker ID for session."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return "wrk_8849"

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return "wrk_8849"

    # Local / Demo tokens
    if token.startswith("gc_") or not supabase:
        return "wrk_8849"

    try:
        response = supabase.auth.get_user(token)
        user = getattr(response, "user", None) or (
            response.get("user") if isinstance(response, dict) else None
        )
        if user:
            user_id = getattr(user, "id", None) or user.get("id")
            if user_id:
                return str(user_id)
    except Exception:
        pass

    return "wrk_8849"
