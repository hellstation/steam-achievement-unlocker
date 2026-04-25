from pathlib import Path

CONFIG_FILE    = Path.home() / ".steam_ach_manager.json"
GAMES_CACHE_FILE = Path.home() / ".steam_ach_manager_games_cache.json"
SCRIPT_DIR     = Path(__file__).parent.parent
LOCAL_DYLIB    = SCRIPT_DIR / "libsteam_api.dylib"

STEAM_API_BASE = "https://api.steampowered.com"

DYLIB_DOWNLOAD_URLS = [
    "https://github.com/neogeek/steamworks-sdk-redistributable/raw/main/osx/libsteam_api.dylib",
    "https://github.com/collaborate-inc/steamworks-sdk-redistributable/raw/master/redistributable_bin/osx/libsteam_api.dylib",
]

STEAMAPPS_PATHS = [
    Path.home() / "Library/Application Support/Steam/steamapps",
    Path("/Users/Shared/Steam/steamapps"),
]
