"""Tests for backend.app.core.config's ENVIRONMENT default resolution.

ENVIRONMENT must default to "production" whenever it is not explicitly
provided, so that a deployment that forgets to set it fails toward the
strict behavior, not the permissive one -- backend/app/api/deps.py's
local-auth fallback depends on this default being correct.

These tests reload the config module under a controlled os.environ
rather than trusting whatever config.ENVIRONMENT already resolved to at
collection time: this repo's own local backend/.env sets
ENVIRONMENT=development for local development, so the already-imported
module is not a reliable source of truth for "what happens when it's
unset". load_dotenv is patched to a no-op during the reload so that
real .env file is never consulted, isolating each test to exactly the
os.environ it sets up.
"""

import importlib

from backend.app.core import config as config_module


def _reload_config_with_env(monkeypatch, **env):
    # config.py re-runs `from dotenv import load_dotenv` on every reload,
    # which would re-fetch (and clobber) a patch applied directly to
    # config_module.load_dotenv. Patching dotenv's own attribute instead
    # ensures the re-import picks up the no-op.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *_args, **_kwargs: None)

    monkeypatch.delenv("ENVIRONMENT", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    importlib.reload(config_module)
    return config_module


class TestEnvironmentDefault:
    def test_environment_defaults_to_production_when_unset(self, monkeypatch):
        reloaded = _reload_config_with_env(monkeypatch)
        assert reloaded.ENVIRONMENT == "production"
        assert reloaded.IS_DEVELOPMENT is False

    def test_environment_explicit_production(self, monkeypatch):
        reloaded = _reload_config_with_env(monkeypatch, ENVIRONMENT="production")
        assert reloaded.ENVIRONMENT == "production"
        assert reloaded.IS_DEVELOPMENT is False

    def test_environment_explicit_development(self, monkeypatch):
        reloaded = _reload_config_with_env(monkeypatch, ENVIRONMENT="development")
        assert reloaded.ENVIRONMENT == "development"
        assert reloaded.IS_DEVELOPMENT is True

    def test_unrecognized_environment_value_is_not_development(self, monkeypatch):
        """No case variants, typos, or unrelated values (e.g. "staging")
        may resolve to development -- only the exact string does."""
        reloaded = _reload_config_with_env(monkeypatch, ENVIRONMENT="Development")
        assert reloaded.IS_DEVELOPMENT is False

    def test_empty_environment_value_defaults_are_not_development(self, monkeypatch):
        """An ENVIRONMENT var that's present but empty (e.g. a deploy
        platform that sets the key with a blank value) must not be
        treated as development."""
        reloaded = _reload_config_with_env(monkeypatch, ENVIRONMENT="")
        assert reloaded.IS_DEVELOPMENT is False
