import argparse
import logging
import os
import platform
import subprocess
import sys
import time

from rich.console import Console

from src.api.steam_web_api import SteamWebAPI
from src.config import load_games_cache, save_games_cache
from src.constants import LOCAL_DYLIB
from src.errors import (
    APIResponseError,
    AppError,
    AuthError,
    ConfigError,
    NetworkError,
    PrivacyError,
)
from src.exit_codes import (
    API_RESPONSE_ERROR,
    AUTH_ERROR,
    CONFIG_ERROR,
    GENERAL_ERROR,
    NETWORK_ERROR,
    PRIVACY_ERROR,
    SUCCESS,
)
from src.logging_utils import setup_logging
from src.steamworks.dylib_manager import setup_dylib
from src.ui.achievement_menu import achievement_menu
from src.ui.credentials import setup_credentials, show_profile
from src.ui.game_selector import load_game_achievements, select_game
from src.ui.header import print_header

console = Console()
logger = logging.getLogger("steam_unlick")


def _ensure_deps():
    missing = []
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import rich
    except ImportError:
        missing.append("rich")

    if not missing:
        return

    print(f"[setup] Устанавливаю зависимости: {', '.join(missing)} ...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + missing)
        print("[setup] Готово. Перезапускаю...\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"[!] Не удалось установить зависимости: {e}")
        print(f"    Выполните вручную: pip3 install {' '.join(missing)}")
        raise SystemExit(CONFIG_ERROR)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Steam Achievement Unlocker")
    parser.add_argument("--api-key", help="Steam Web API Key (32 hex)")
    parser.add_argument("--steam-id", help="SteamID64 (17 digits)")
    parser.add_argument("--auto-refresh", type=int, help="Auto refresh interval in seconds")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--non-interactive", action="store_true", help="Load library once and exit")
    return parser.parse_args(argv)


def _get_auto_refresh_interval(explicit: int | None) -> int:
    if explicit is not None:
        return max(0, explicit)

    raw = os.getenv("STEAM_AUTO_REFRESH_SECONDS", "120").strip()
    try:
        value = int(raw)
    except ValueError:
        logger.warning("invalid_auto_refresh_env_value", extra={"value": raw})
        return 120
    return max(0, value)


def _dedupe_games(games: list) -> list:
    by_appid = {}
    for game in games:
        app_id = game.get("appid")
        if app_id is None:
            continue
        old = by_appid.get(app_id)
        if not old or game.get("playtime_forever", 0) >= old.get("playtime_forever", 0):
            by_appid[app_id] = game
    return sorted(by_appid.values(), key=lambda g: g.get("playtime_forever", 0), reverse=True)


def _load_games_with_cache(api: SteamWebAPI, steam_id: str) -> tuple[list, str]:
    cache = load_games_cache()
    cached_games = cache.get(steam_id, {}).get("games", [])

    try:
        live_games = api.get_owned_games()
    except NetworkError as e:
        logger.warning(
            "owned_games_live_fetch_failed",
            extra={"steam_id": steam_id, "cached_count": len(cached_games), "error": str(e)},
        )
        if cached_games:
            return _dedupe_games(cached_games), f"кэш (API недоступен: {e})"
        raise

    if live_games:
        merged = _dedupe_games(live_games + cached_games)
        cache[steam_id] = {"updated_at": int(time.time()), "games": merged}
        save_games_cache(cache)
        logger.info("owned_games_loaded", extra={"steam_id": steam_id, "source": "live_plus_cache", "count": len(merged)})
        return merged, "Steam API + кэш"

    if cached_games:
        logger.warning(
            "owned_games_empty_live_using_cache",
            extra={"steam_id": steam_id, "cached_count": len(cached_games)},
        )
        return _dedupe_games(cached_games), "кэш (Steam API вернул пустой список)"

    logger.warning("owned_games_empty_no_cache", extra={"steam_id": steam_id})
    return [], "Steam API"


def _refresh_games(api: SteamWebAPI, steam_id: str, games: list) -> list:
    prev_count = len(games)
    with console.status("Запрашиваю актуальный список у Steam API..."):
        try:
            new_games, source = _load_games_with_cache(api, steam_id)
        except AppError as e:
            logger.warning("games_refresh_failed", extra={"steam_id": steam_id, "error": str(e)})
            return games

    logger.info(
        "games_refreshed",
        extra={
            "steam_id": steam_id,
            "prev_count": prev_count,
            "new_count": len(new_games),
            "source": source,
        },
    )

    if len(new_games) > prev_count:
        loaded_at = time.strftime("%H:%M:%S")
        console.print(
            f"[green]✓ Обновлено: {len(new_games)} игр (+{len(new_games)-prev_count} новых), "
            f"источник: {source}, {loaded_at}[/green]"
        )
    return new_games


def _run_app(args: argparse.Namespace) -> int:
    global logger
    logger = setup_logging(args.log_level)
    logger.info("app_start")

    print_header()
    arch = platform.machine()
    macos = platform.mac_ver()[0]
    console.print(f"[dim]macOS {macos} · {arch} · Python {sys.version.split()[0]}[/dim]\n")

    if LOCAL_DYLIB.exists():
        console.print(f"[green]✓[/green] Steamworks SDK: [dim]{LOCAL_DYLIB.name}[/dim]")
    else:
        setup_dylib()
    console.print()

    api_key, steam_id = setup_credentials(
        api_key_override=args.api_key,
        steam_id_override=args.steam_id,
        non_interactive=args.non_interactive,
    )
    logger.info("credentials_loaded", extra={"steam_id_suffix": steam_id[-6:] if steam_id else ""})

    api = SteamWebAPI(api_key, steam_id)
    profile = show_profile(api)

    console.print()
    with console.status("Загрузка библиотеки Steam..."):
        games, source = _load_games_with_cache(api, steam_id)

    if not games and profile and profile.get("communityvisibilitystate", 0) < 3:
        raise PrivacyError("Профиль Steam не публичный: откройте 'Детали игры' в настройках приватности")

    loaded_at = time.strftime("%H:%M:%S")
    logger.info("games_loaded_for_ui", extra={"steam_id": steam_id, "count": len(games), "source": source})
    console.print(f"[green]✓[/green] Загружено {len(games)} игр [dim]({source}, {loaded_at})[/dim]")

    auto_refresh_seconds = _get_auto_refresh_interval(args.auto_refresh)
    if auto_refresh_seconds > 0:
        console.print(f"[dim]↻ Автообновление библиотеки включено: каждые {auto_refresh_seconds} сек[/dim]")
    else:
        console.print("[dim]↻ Автообновление библиотеки выключено[/dim]")

    console.print(
        "[dim]⚠ Steam API кэширует список игр на своих серверах — "
        "новая игра может не появляться несколько минут/часов после добавления[/dim]"
    )

    if args.non_interactive:
        logger.info("non_interactive_done", extra={"count": len(games), "source": source})
        return SUCCESS

    last_auto_refresh_at = time.time()
    while True:
        if auto_refresh_seconds > 0 and (time.time() - last_auto_refresh_at) >= auto_refresh_seconds:
            games = _refresh_games(api, steam_id, games)
            last_auto_refresh_at = time.time()

        try:
            game = select_game(games)
        except KeyboardInterrupt:
            logger.info("app_exit_keyboard_interrupt")
            console.print("\n[dim]Выход.[/dim]")
            return SUCCESS

        if not game:
            continue

        logger.info(
            "game_selected",
            extra={"steam_id": steam_id, "app_id": game.get("appid"), "game_name": game.get("name", "")},
        )
        console.print(f"\n[bold]Игра:[/bold] {game.get('name')} (AppID: {game['appid']})")
        achievements = load_game_achievements(api, game)

        if not achievements:
            logger.warning(
                "game_has_no_achievements_or_unavailable",
                extra={"steam_id": steam_id, "app_id": game.get("appid")},
            )
            console.print("[yellow]У этой игры нет достижений или они недоступны[/yellow]")
            continue

        try:
            achievement_menu(api, game, achievements)
        except KeyboardInterrupt:
            logger.info("achievement_menu_interrupted", extra={"steam_id": steam_id, "app_id": game.get("appid")})
            console.print("\n[dim]Возврат к выбору игры.[/dim]")
            continue


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return _run_app(args)
    except KeyboardInterrupt:
        console.print("\n[dim]Выход.[/dim]")
        return SUCCESS
    except AuthError as e:
        console.print(f"[red]Ошибка авторизации:[/red] {e}")
        return AUTH_ERROR
    except PrivacyError as e:
        console.print(f"[yellow]Ошибка приватности:[/yellow] {e}")
        return PRIVACY_ERROR
    except NetworkError as e:
        console.print(f"[red]Сетевая ошибка:[/red] {e}")
        return NETWORK_ERROR
    except APIResponseError as e:
        console.print(f"[red]Ошибка ответа API:[/red] {e}")
        return API_RESPONSE_ERROR
    except ConfigError as e:
        console.print(f"[red]Ошибка конфигурации:[/red] {e}")
        return CONFIG_ERROR
    except Exception as e:
        logger.exception("fatal_unhandled_error")
        console.print(f"[red]Неожиданная ошибка:[/red] {e}")
        return GENERAL_ERROR


def cli() -> None:
    _ensure_deps()
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    cli()
