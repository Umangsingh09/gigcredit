"""Unit tests for backend.app.api.deps.get_current_user_id.

Calls the dependency function directly (it's a plain function that only
happens to use FastAPI's Header() as a default) so these tests do not
need a running app or TestClient. `backend.app.api.deps.supabase` is
monkeypatched per-test to simulate the "no Supabase project configured"
state (None) and the "real Supabase project configured" state (a fake
client), since that module-level binding is what the dependency actually
reads.
"""

import pytest
from fastapi import HTTPException

from backend.app.api import deps


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeAuthResponse:
    def __init__(self, user):
        self.user = user


class _FakeSupabaseAuth:
    def __init__(self, get_user_result=None, get_user_exception=None):
        self._result = get_user_result
        self._exception = get_user_exception

    def get_user(self, token):
        if self._exception is not None:
            raise self._exception
        return self._result


class _FakeSupabaseClient:
    def __init__(self, get_user_result=None, get_user_exception=None):
        self.auth = _FakeSupabaseAuth(get_user_result, get_user_exception)


class TestMissingOrMalformedToken:
    def test_missing_authorization_header_is_rejected(self):
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization=None)
        assert exc_info.value.status_code == 401

    def test_authorization_without_bearer_prefix_is_rejected(self):
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Token abc123")
        assert exc_info.value.status_code == 401

    def test_bearer_with_empty_token_is_rejected(self):
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer ")
        assert exc_info.value.status_code == 401


class TestInvalidTokenWithSupabaseConfigured:
    def test_get_user_raising_is_rejected(self, monkeypatch):
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(get_user_exception=Exception("invalid jwt")),
        )
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer not-a-real-token")
        assert exc_info.value.status_code == 401

    def test_get_user_returning_no_user_is_rejected(self, monkeypatch):
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(get_user_result=_FakeAuthResponse(user=None)),
        )
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer expired-token")
        assert exc_info.value.status_code == 401

    def test_arbitrary_long_token_is_rejected_when_supabase_configured(self, monkeypatch):
        """Regression guard: a long/plausible-looking token must never be
        accepted just because it's long — every request goes through real
        Supabase verification whenever a project is configured.
        """
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(get_user_exception=Exception("invalid jwt")),
        )
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(
                authorization="Bearer this-is-a-very-long-plausible-looking-token-123456"
            )
        assert exc_info.value.status_code == 401


class TestValidSupabaseToken:
    def test_valid_token_returns_user_id(self, monkeypatch):
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(
                get_user_result=_FakeAuthResponse(user=_FakeUser("11111111-1111-1111-1111-111111111111"))
            ),
        )
        user_id = deps.get_current_user_id(authorization="Bearer a-real-supabase-jwt")
        assert user_id == "11111111-1111-1111-1111-111111111111"

    def test_dict_shaped_response_is_also_supported(self, monkeypatch):
        """supabase-py has returned both object-shaped and dict-shaped
        responses across versions; both must resolve correctly."""
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(get_user_result={"user": {"id": "user-abc"}}),
        )
        user_id = deps.get_current_user_id(authorization="Bearer a-real-supabase-jwt")
        assert user_id == "user-abc"


class TestLocalDevFallback:
    """The fallback is scoped to exactly the token shape /auth/register
    and /auth/login issue when no Supabase project is configured, and
    must never activate once Supabase is configured.
    """

    def test_local_token_accepted_when_supabase_not_configured(self, monkeypatch):
        monkeypatch.setattr(deps, "supabase", None)
        user_id = deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert user_id == "worker@example.com"

    def test_non_local_token_rejected_when_supabase_not_configured(self, monkeypatch):
        """This is the critical regression test: without Supabase
        configured, nothing except the exact local- token shape may be
        accepted — a long/plausible-looking arbitrary token must still
        be rejected.
        """
        monkeypatch.setattr(deps, "supabase", None)
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(
                authorization="Bearer this-is-a-very-long-plausible-looking-token-123456"
            )
        assert exc_info.value.status_code == 401

    def test_bare_local_prefix_with_no_email_is_rejected(self, monkeypatch):
        monkeypatch.setattr(deps, "supabase", None)
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-")
        assert exc_info.value.status_code == 401

    def test_local_shaped_token_is_ignored_when_supabase_is_configured(self, monkeypatch):
        """The fallback must never trigger once a real Supabase project
        is configured, even if a client sends a local-shaped token — it
        must go through real verification (and fail, since it isn't a
        real Supabase JWT).
        """
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(get_user_exception=Exception("invalid jwt")),
        )
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert exc_info.value.status_code == 401
