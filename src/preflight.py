from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import dataclass, field


@dataclass
class PreflightResult:
    ok: bool
    steam_running: bool
    python_ok: bool
    platform_ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def is_steam_running() -> bool:
    """Return True if the Steam client process appears to be running on macOS."""
    try:
        r = subprocess.run(
            ["pgrep", "-x", "steam_osx"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode == 0 and r.stdout.strip():
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # Fallback: any process matching "Steam" (PID list only)
    try:
        r = subprocess.run(
            ["pgrep", "-if", "Steam"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return r.returncode == 0 and bool(r.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def run_preflight(
    *,
    platform_system: str | None = None,
    python_version_info: tuple | None = None,
    steam_running: bool | None = None,
) -> PreflightResult:
    system = platform_system if platform_system is not None else platform.system()
    version = python_version_info if python_version_info is not None else sys.version_info
    steam = is_steam_running() if steam_running is None else steam_running

    errors: list[str] = []
    warnings: list[str] = []

    platform_ok = system == "Darwin"
    if not platform_ok:
        errors.append(
            f"Этот инструмент поддерживает только macOS (сейчас: {system})."
        )

    python_ok = version >= (3, 10)
    if not python_ok:
        ver = f"{version[0]}.{version[1]}"
        errors.append(f"Нужен Python 3.10 или новее (сейчас: {ver}).")

    if not steam:
        errors.append(
            "Клиент Steam не запущен. Откройте Steam, войдите в аккаунт и запустите скрипт снова."
        )

    ok = platform_ok and python_ok and steam
    return PreflightResult(
        ok=ok,
        steam_running=steam,
        python_ok=python_ok,
        platform_ok=platform_ok,
        errors=errors,
        warnings=warnings,
    )
