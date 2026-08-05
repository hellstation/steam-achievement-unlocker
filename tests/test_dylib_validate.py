from pathlib import Path

from src.steamworks.dylib_manager import validate_dylib


def test_validate_dylib_missing(tmp_path: Path):
    ok, reason = validate_dylib(tmp_path / "nope.dylib")
    assert ok is False
    assert reason


def test_validate_dylib_too_small(tmp_path: Path):
    p = tmp_path / "libsteam_api.dylib"
    p.write_bytes(b"tiny")
    ok, reason = validate_dylib(p)
    assert ok is False
    assert "100" in reason or "маленьк" in reason.lower() or "small" in reason.lower() or "KB" in reason


def test_validate_dylib_html_rejected(tmp_path: Path):
    p = tmp_path / "libsteam_api.dylib"
    p.write_bytes(b"<!DOCTYPE html>" + b"x" * (120 * 1024))
    ok, reason = validate_dylib(p)
    assert ok is False


def test_validate_dylib_accepts_large_binaryish(tmp_path: Path):
    p = tmp_path / "libsteam_api.dylib"
    p.write_bytes(b"\xcf\xfa\xed\xfe" + b"\x00" * (120 * 1024))
    ok, reason = validate_dylib(p, host_machine="arm64")
    assert ok is True
    assert reason == ""
