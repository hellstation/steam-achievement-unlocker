import main
from src.errors import NetworkError


def test_dedupe_games_keeps_highest_playtime():
    games = [
        {"appid": 10, "name": "A", "playtime_forever": 20},
        {"appid": 10, "name": "A", "playtime_forever": 40},
        {"appid": 20, "name": "B", "playtime_forever": 5},
    ]
    result = main._dedupe_games(games)
    assert len(result) == 2
    assert result[0]["appid"] == 10
    assert result[0]["playtime_forever"] == 40


def test_load_games_with_cache_uses_live_and_saves(monkeypatch):
    class API:
        def get_owned_games(self):
            return [{"appid": 1, "name": "Live", "playtime_forever": 10}]

    monkeypatch.setattr(main, "load_games_cache", lambda: {"sid": {"games": [{"appid": 1, "name": "Old", "playtime_forever": 1}]}})
    saved = {}
    monkeypatch.setattr(main, "save_games_cache", lambda payload: saved.update(payload))

    games, source = main._load_games_with_cache(API(), "sid")
    assert source == "Steam API + кэш"
    assert len(games) == 1
    assert games[0]["playtime_forever"] == 10
    assert "sid" in saved


def test_load_games_with_cache_network_falls_back_to_cache(monkeypatch):
    class API:
        def get_owned_games(self):
            raise NetworkError("boom")

    monkeypatch.setattr(main, "load_games_cache", lambda: {"sid": {"games": [{"appid": 2, "name": "Cache", "playtime_forever": 2}]}})
    monkeypatch.setattr(main, "save_games_cache", lambda payload: None)

    games, source = main._load_games_with_cache(API(), "sid")
    assert len(games) == 1
    assert "кэш" in source


def test_auto_refresh_interval_prefers_cli_over_env(monkeypatch):
    monkeypatch.setenv("STEAM_AUTO_REFRESH_SECONDS", "999")
    assert main._get_auto_refresh_interval(30) == 30


def test_auto_refresh_interval_uses_default_on_invalid_env(monkeypatch):
    monkeypatch.setenv("STEAM_AUTO_REFRESH_SECONDS", "abc")
    assert main._get_auto_refresh_interval(None) == 120
