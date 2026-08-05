import json
from pathlib import Path
import os

from .constants import CONFIG_FILE, GAMES_CACHE_FILE


def _read_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def load_config() -> dict:
    return _read_json(CONFIG_FILE, {})


def save_config(cfg: dict):
    _write_json(CONFIG_FILE, cfg)


def load_games_cache() -> dict:
    return _read_json(GAMES_CACHE_FILE, {})


def save_games_cache(cache: dict):
    _write_json(GAMES_CACHE_FILE, cache)
