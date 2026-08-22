"""deps

Shared FastAPI dependencies for authenticated routes.
"""

from fastapi import Header, HTTPException

from backend.app.core.supabase import supabase


_LOCAL_TOKEN_PREFIX = "local-"


def get_current_user_id(authorization: str = Header(None)) -> str:
    """Resolve the authenticated Supabase user id from a Bearer token.

    Verification is delegated to Supabase Auth itself
    (supabase.auth.get_user) rather than decoding the JWT locally, so
    this stays correct regardless of which signing key/algorithm
    Supabase issues tokens with, and never requires the service-role key
    or any signing secret to live in backend code.

    Local-dev fallback: this function accepts a "local-<email>" token
    ONLY when no Supabase project is configured at all (`supabase` is
    None — see backend/app/core/supabase.py, SUPABASE_ENABLED). That is
    exactly the token shape /auth/register and /auth/login themselves
    issue in that same no-Supabase mode, and no other token value is
    accepted there. The instant real Supabase credentials are
    configured, `supabase` is no longer None and this branch is
    unreachable — every request is verified against Supabase Auth, with
    no bypass of any kind. This must never be widened to accept
    arbitrary tokens or to run when `supabase` is configured.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    if supabase is None:
        if token.startswith(_LOCAL_TOKEN_PREFIX) and len(token) > len(_LOCAL_TOKEN_PREFIX):
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
