"""HTTP tests for POST /auth/register and POST /auth/login.

Exercises the real FastAPI app via TestClient. `backend.app.api.auth.supabase`
and `backend.app.api.auth.ENVIRONMENT` are monkeypatched per-test to
simulate every combination of "Supabase unavailable" vs. "Supabase
configured" and "development" vs. "production"/unset ENVIRONMENT --
mirroring the same two-condition gate covered for token verification in
backend/tests/api/test_deps.py. `local_users` (the in-memory fallback
store) is reset to a fresh dict per test so registrations from one test
never leak into another.
"""

from fastapi.testclient import TestClient

from backend.app.api import auth
from backend.app.main import app

client = TestClient(app)


class _FakeUser:
    def __init__(self, user_id, email, user_metadata=None):
        self.id = user_id
        self.email = email
        self.user_metadata = user_metadata or {}


class _FakeSession:
    def __init__(self, access_token):
        self.access_token = access_token


class _FakeAuthResponse:
    def __init__(self, user=None, session=None):
        self.user = user
        self.session = session


class _FakeAuthAPI:
    def __init__(self, sign_up_result=None, sign_in_result=None):
        self._sign_up_result = sign_up_result
        self._sign_in_result = sign_in_result

    def sign_up(self, payload):
        return self._sign_up_result

    def sign_in_with_password(self, payload):
        return self._sign_in_result


class _FakeSupabaseClient:
    def __init__(self, sign_up_result=None, sign_in_result=None):
        self.auth = _FakeAuthAPI(sign_up_result, sign_in_result)


def _reset_local_users(monkeypatch):
    monkeypatch.setattr(auth, "local_users", {})


class TestLocalAuthFallbackRequiresDevelopment:
    """The in-memory local register/login fallback may only run when
    BOTH supabase is None AND ENVIRONMENT == "development" -- neither
    condition alone is enough, matching deps.py's gate on token
    verification.
    """

    def test_register_fallback_works_in_development_when_supabase_unavailable(self, monkeypatch):
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "development")

        response = client.post(
            "/auth/register",
            json={"full_name": "Dev Worker", "email": "dev@example.com", "password": "secret123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "local-dev@example.com"
        assert body["email"] == "dev@example.com"

    def test_login_fallback_works_in_development_when_supabase_unavailable(self, monkeypatch):
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "development")

        client.post(
            "/auth/register",
            json={"full_name": "Dev Worker", "email": "dev@example.com", "password": "secret123"},
        )
        response = client.post(
            "/auth/login", json={"email": "dev@example.com", "password": "secret123"}
        )

        assert response.status_code == 200
        assert response.json()["access_token"] == "local-dev@example.com"

    def test_register_fallback_rejected_in_production_when_supabase_unavailable(self, monkeypatch):
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/register",
            json={"full_name": "Prod User", "email": "prod@example.com", "password": "secret123"},
        )

        assert response.status_code == 503
        assert auth.local_users == {}

    def test_login_fallback_rejected_in_production_when_supabase_unavailable(self, monkeypatch):
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/login", json={"email": "prod@example.com", "password": "secret123"}
        )

        assert response.status_code == 503

    def test_register_fallback_rejected_when_environment_unset(self, monkeypatch):
        """Simulates a deployment that never set ENVIRONMENT at all.
        auth.ENVIRONMENT mirrors config.ENVIRONMENT's own default
        ("production" -- see backend/tests/core/test_config.py), so
        setting it to "production" here reproduces exactly what an
        unset ENVIRONMENT resolves to.
        """
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/register",
            json={"full_name": "Nobody", "email": "nobody@example.com", "password": "secret123"},
        )

        assert response.status_code == 503

    def test_login_fallback_rejected_when_environment_unset(self, monkeypatch):
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/login", json={"email": "nobody@example.com", "password": "secret123"}
        )

        assert response.status_code == 503

    def test_register_fallback_rejected_for_unrecognized_environment_value(self, monkeypatch):
        """Only the exact string "development" opts in."""
        _reset_local_users(monkeypatch)
        monkeypatch.setattr(auth, "supabase", None)
        monkeypatch.setattr(auth, "ENVIRONMENT", "Development")

        response = client.post(
            "/auth/register",
            json={"full_name": "Nobody", "email": "typo@example.com", "password": "secret123"},
        )

        assert response.status_code == 503


class TestRealSupabaseAuthUnaffected:
    """Real Supabase registration/login must behave identically
    regardless of ENVIRONMENT -- the ENVIRONMENT gate only applies to
    the no-Supabase fallback branch, and must never be consulted (let
    alone block anything) once Supabase is actually configured.
    """

    def test_register_uses_real_supabase_when_configured_in_production(self, monkeypatch):
        fake_user = _FakeUser("11111111-1111-1111-1111-111111111111", "real@example.com")
        fake_session = _FakeSession("real-supabase-access-token")
        monkeypatch.setattr(
            auth,
            "supabase",
            _FakeSupabaseClient(sign_up_result=_FakeAuthResponse(user=fake_user, session=fake_session)),
        )
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/register",
            json={"full_name": "Real User", "email": "real@example.com", "password": "secret123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "real-supabase-access-token"
        assert body["user_id"] == "11111111-1111-1111-1111-111111111111"

    def test_register_uses_real_supabase_when_configured_in_development(self, monkeypatch):
        """Even with ENVIRONMENT=development, a configured Supabase
        client is what handles registration -- the local fallback branch
        is only reachable when supabase is None."""
        fake_user = _FakeUser("22222222-2222-2222-2222-222222222222", "real2@example.com")
        fake_session = _FakeSession("real-supabase-access-token-2")
        monkeypatch.setattr(
            auth,
            "supabase",
            _FakeSupabaseClient(sign_up_result=_FakeAuthResponse(user=fake_user, session=fake_session)),
        )
        monkeypatch.setattr(auth, "ENVIRONMENT", "development")

        response = client.post(
            "/auth/register",
            json={"full_name": "Real User", "email": "real2@example.com", "password": "secret123"},
        )

        assert response.status_code == 200
        assert response.json()["access_token"] == "real-supabase-access-token-2"

    def test_login_uses_real_supabase_when_configured_in_production(self, monkeypatch):
        fake_user = _FakeUser(
            "33333333-3333-3333-3333-333333333333",
            "real3@example.com",
            user_metadata={"full_name": "Real Three"},
        )
        fake_session = _FakeSession("real-supabase-login-token")
        monkeypatch.setattr(
            auth,
            "supabase",
            _FakeSupabaseClient(sign_in_result=_FakeAuthResponse(user=fake_user, session=fake_session)),
        )
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/login", json={"email": "real3@example.com", "password": "secret123"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "real-supabase-login-token"
        assert body["full_name"] == "Real Three"

    def test_login_invalid_credentials_still_rejected_when_supabase_configured(self, monkeypatch):
        """Real Supabase auth failures must still surface as 401, not be
        swallowed or altered by the ENVIRONMENT gate."""
        monkeypatch.setattr(
            auth,
            "supabase",
            _FakeSupabaseClient(sign_in_result=_FakeAuthResponse(user=None, session=None)),
        )
        monkeypatch.setattr(auth, "ENVIRONMENT", "production")

        response = client.post(
            "/auth/login", json={"email": "nobody@example.com", "password": "wrong"}
        )

        assert response.status_code == 401
