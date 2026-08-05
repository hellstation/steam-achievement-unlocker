from src.steamworks.ctypes_wrapper import SteamworksCtypes


def test_shutdown_removes_appid_file(tmp_path, monkeypatch):
    sw = SteamworksCtypes()
    appid = tmp_path / "steam_appid.txt"
    monkeypatch.setattr(sw, "_appid_file", appid)
    appid.write_text("730")
    sw._lib = None
    sw.initialized = True
    sw.shutdown()
    assert not appid.exists()
    assert sw.initialized is False


def test_init_failure_cleans_appid(tmp_path, monkeypatch):
    sw = SteamworksCtypes()
    appid = tmp_path / "steam_appid.txt"
    monkeypatch.setattr(sw, "_appid_file", appid)

    bad = tmp_path / "missing.dylib"
    ok, _info = sw.init(730, bad)
    assert ok is False
    sw.shutdown()
    assert not appid.exists()
