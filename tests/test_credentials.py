import pytest

from src.errors import ConfigError
from src.ui import credentials


def test_validators():
    assert credentials._is_valid_api_key("a" * 32)
    assert not credentials._is_valid_api_key("a" * 31)
    assert credentials._is_valid_steam_id("76561197989341403")
    assert not credentials._is_valid_steam_id("123")


def test_setup_credentials_override_valid(monkeypatch):
    saved = {}
    monkeypatch.setattr(credentials, "save_config", lambda cfg: saved.update(cfg))

    api_key = "a" * 32
    steam_id = "76561197989341403"
    result = credentials.setup_credentials(api_key_override=api_key, steam_id_override=steam_id, non_interactive=True)

    assert result == (api_key, steam_id)
    assert saved["api_key"] == api_key
    assert saved["steam_id"] == steam_id


def test_setup_credentials_override_invalid_raises():
    with pytest.raises(ConfigError):
        credentials.setup_credentials(api_key_override="bad", steam_id_override="123", non_interactive=True)
