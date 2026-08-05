from src.preflight import run_preflight


def test_preflight_requires_macos():
    result = run_preflight(
        platform_system="Linux",
        python_version_info=(3, 12, 0),
        steam_running=True,
    )
    assert result.ok is False
    assert result.platform_ok is False
    assert any("macOS" in e or "macos" in e.lower() for e in result.errors)


def test_preflight_requires_python_310():
    result = run_preflight(
        platform_system="Darwin",
        python_version_info=(3, 9, 0),
        steam_running=True,
    )
    assert result.ok is False
    assert result.python_ok is False
    assert any("3.10" in e for e in result.errors)


def test_preflight_steam_not_running():
    result = run_preflight(
        platform_system="Darwin",
        python_version_info=(3, 12, 0),
        steam_running=False,
    )
    assert result.ok is False
    assert result.steam_running is False
    assert any("Steam" in e for e in result.errors)


def test_preflight_all_ok():
    result = run_preflight(
        platform_system="Darwin",
        python_version_info=(3, 12, 0),
        steam_running=True,
    )
    assert result.ok is True
    assert result.platform_ok is True
    assert result.python_ok is True
    assert result.steam_running is True
    assert result.errors == []
