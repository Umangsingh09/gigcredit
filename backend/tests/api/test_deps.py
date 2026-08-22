"""Unit tests for backend.app.api.deps.get_current_user_id.

Calls the dependency function directly (it's a plain function that only
happens to use FastAPI's Header() as a default) so these tests do not
need a running app or TestClient. `backend.app.api.deps.supabase` and
`backend.app.api.deps.ENVIRONMENT` are monkeypatched per-test to
simulate every combination of "no Supabase project configured" (None)
vs. "real Supabase project configured" (a fake client), and
"development" vs. "production"/unset ENVIRONMENT, since those two
module-level bindings are what the dependency actually reads. See
backend/tests/core/test_config.py for coverage of ENVIRONMENT's own
default-resolution logic in backend.app.core.config.
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
    requires BOTH `supabase is None` AND ENVIRONMENT == "development"
    (deps.ENVIRONMENT, imported from backend.app.core.config, which
    itself defaults to "production" when unset — see
    backend/tests/core/test_config.py for that default's own coverage).
    Neither condition alone is enough.
    """

    # --- ENVIRONMENT gate: supabase unavailable, but not (only) in development ---

    def test_local_token_rejected_when_environment_unset(self, monkeypatch):
        """Simulates a deployment that never set ENVIRONMENT at all.
        deps.ENVIRONMENT mirrors config.ENVIRONMENT's own default
        ("production"), so setting it to "production" here reproduces
        exactly what an unset ENVIRONMENT resolves to.
        """
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "production")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert exc_info.value.status_code == 401

    def test_local_token_rejected_when_environment_is_production(self, monkeypatch):
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "production")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert exc_info.value.status_code == 401

    def test_local_token_rejected_for_unrecognized_environment_value(self, monkeypatch):
        """Only the exact string "development" opts in — no case
        variants, typos, or other values (e.g. "staging") may enable
        the fallback."""
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "Development")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert exc_info.value.status_code == 401

    # --- both conditions satisfied ---

    def test_local_token_accepted_when_development_and_supabase_not_configured(self, monkeypatch):
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "development")
        user_id = deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert user_id == "worker@example.com"

    def test_bare_local_prefix_with_no_email_is_rejected_even_in_development(self, monkeypatch):
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "development")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-")
        assert exc_info.value.status_code == 401

    def test_non_local_token_rejected_in_development_when_supabase_not_configured(self, monkeypatch):
        """Critical regression test: even fully opted into development
        mode with Supabase unavailable, nothing except the exact
        local-<email> shape may be accepted — a long/plausible-looking
        arbitrary token must still be rejected.
        """
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "development")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(
                authorization="Bearer this-is-a-very-long-plausible-looking-token-123456"
            )
        assert exc_info.value.status_code == 401

    def test_non_local_token_rejected_in_production_when_supabase_not_configured(self, monkeypatch):
        """Same arbitrary-token regression guard, in production mode."""
        monkeypatch.setattr(deps, "supabase", None)
        monkeypatch.setattr(deps, "ENVIRONMENT", "production")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(
                authorization="Bearer this-is-a-very-long-plausible-looking-token-123456"
            )
        assert exc_info.value.status_code == 401

    # --- supabase configured: fallback must never trigger, regardless of ENVIRONMENT ---

    def test_local_shaped_token_ignored_when_supabase_configured_in_production(self, monkeypatch):
        """The fallback must never trigger once a real Supabase project
        is configured, even if a client sends a local-shaped token — it
        must go through real verification (and fail, since it isn't a
        real Supabase JWT)."""
        monkeypatch.setattr(
            deps,
            "supabase",
            _FakeSupabaseClient(get_user_exception=Exception("invalid jwt")),
        )
        monkeypatch.setattr(deps, "ENVIRONMENT", "production")
        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-worker@example.com")
        assert exc_info.value.status_code == 401

    def test_local_shaped_token_ignored_and_real_verification_attempted_even_in_development(
        self, monkeypatch
    ):
        """Even with ENVIRONMENT=development, once Supabase IS
        configured, real verification is what runs — proven here by a
        fake client whose get_user() would return a valid user for any
        token, including a local-shaped one. If the fallback were
        wrongly checked first (or supabase not consulted at all), this
        would still pass by coincidence; the real proof is the next
        test, which asserts get_user was actually called.
        """
        fake_client = _FakeSupabaseClient(
            get_user_result=_FakeAuthResponse(user=_FakeUser("real-supabase-user-id"))
        )
        monkeypatch.setattr(deps, "supabase", fake_client)
        monkeypatch.setattr(deps, "ENVIRONMENT", "development")

        user_id = deps.get_current_user_id(authorization="Bearer local-worker@example.com")

        # Proves real Supabase verification ran (not the local fallback):
        # the returned id is Supabase's user id, not the "worker@example.com"
        # the local fallback would have derived from the token itself.
        assert user_id == "real-supabase-user-id"

    def test_real_verification_is_actually_invoked_when_supabase_configured_in_development(
        self, monkeypatch
    ):
        """Directly asserts supabase.auth.get_user was called — proving
        the code path went through real verification rather than the
        local fallback, even though ENVIRONMENT=development and the
        token happens to be local-shaped.
        """
        calls = []

        class _RecordingAuth:
            def get_user(self, token):
                calls.append(token)
                raise Exception("invalid jwt")

        class _RecordingClient:
            auth = _RecordingAuth()

        monkeypatch.setattr(deps, "supabase", _RecordingClient())
        monkeypatch.setattr(deps, "ENVIRONMENT", "development")

        with pytest.raises(HTTPException) as exc_info:
            deps.get_current_user_id(authorization="Bearer local-worker@example.com")

        assert exc_info.value.status_code == 401
        assert calls == ["local-worker@example.com"]
