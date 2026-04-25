import shutil
import logging
from pathlib import Path

import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..constants import LOCAL_DYLIB, DYLIB_DOWNLOAD_URLS, STEAMAPPS_PATHS

console = Console()
logger = logging.getLogger("steam_unlick.steamworks.dylib")


def _search_dylib_locally() -> Path | None:
    candidates = []

    for steamapps in STEAMAPPS_PATHS:
        if steamapps.exists():
            for dylib in steamapps.rglob("libsteam_api.dylib"):
                candidates.append(dylib)

    for p in [
        Path("/Applications/Steam.app/Contents/MacOS/libsteam_api.dylib"),
        Path.home() / "Applications/Steam.app/Contents/MacOS/libsteam_api.dylib",
    ]:
        if p.exists():
            candidates.append(p)

    return candidates[0] if candidates else None


def _download_dylib() -> bool:
    console.print("[dim]Скачиваю libsteam_api.dylib...[/dim]")
    for url in DYLIB_DOWNLOAD_URLS:
        try:
            r = requests.get(url, timeout=30, stream=True)
            if r.status_code == 200:
                with open(LOCAL_DYLIB, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                size_kb = LOCAL_DYLIB.stat().st_size // 1024
                if size_kb < 100:
                    LOCAL_DYLIB.unlink(missing_ok=True)
                    logger.warning("dylib_download_too_small", extra={"url": url, "size_kb": size_kb})
                    continue
                console.print(f"[green]✓ Скачано ({size_kb} KB)[/green]")
                logger.info("dylib_download_ok", extra={"url": url, "size_kb": size_kb, "path": str(LOCAL_DYLIB)})
                return True
        except Exception as e:
            logger.warning("dylib_download_failed", extra={"url": url, "error": str(e)})
            console.print(f"[dim]  {url[:60]}... — ошибка: {e}[/dim]")
            continue
    return False


def setup_dylib() -> bool:
    if LOCAL_DYLIB.exists():
        return True

    console.print("\n[bold]Поиск Steamworks библиотеки...[/bold]")

    with console.status("Сканирую Steam..."):
        found = _search_dylib_locally()

    if found:
        console.print(f"[green]✓ Найдена:[/green] {found}")
        shutil.copy2(found, LOCAL_DYLIB)
        logger.info("dylib_found_local", extra={"source_path": str(found), "target_path": str(LOCAL_DYLIB)})
        console.print("[green]✓ Скопирована в папку скрипта[/green]")
        return True

    console.print("[yellow]Локально не найдена — пробую скачать...[/yellow]")

    if _download_dylib():
        return True

    console.print(Panel(
        "[bold]Не удалось найти или скачать libsteam_api.dylib автоматически.[/bold]\n\n"
        "Установите любую игру через Steam, затем выполните:\n"
        "[cyan]find ~/Library/Application\\ Support/Steam -name 'libsteam_api.dylib'[/cyan]\n\n"
        "И введите найденный путь ниже.",
        style="yellow", title="Ручная установка"
    ))
    manual = Prompt.ask("Путь к libsteam_api.dylib (Enter — пропустить)", default="")
    if manual:
        p = Path(manual.strip())
        if p.exists():
            shutil.copy2(p, LOCAL_DYLIB)
            logger.info("dylib_set_manual", extra={"source_path": str(p), "target_path": str(LOCAL_DYLIB)})
            console.print("[green]✓ Скопирована[/green]")
            return True
        else:
            logger.warning("dylib_manual_not_found", extra={"input_path": str(p)})
            console.print("[red]Файл не найден[/red]")

    logger.error("dylib_unavailable")
    console.print("[yellow]⚠ Продолжаю без dylib — чтение достижений будет работать, запись — нет[/yellow]")
    return False


def find_dylib_for_game(app_id: int) -> Path | None:
    for steamapps in STEAMAPPS_PATHS:
        if not steamapps.exists():
            continue
        acf = steamapps / f"appmanifest_{app_id}.acf"
        if not acf.exists():
            continue
        install_dir = None
        for line in acf.read_text(errors="ignore").splitlines():
            if '"installdir"' in line.lower():
                parts = line.split('"')
                if len(parts) >= 4:
                    install_dir = parts[3]
                    break
        if install_dir:
            dylib = steamapps / "common" / install_dir / "libsteam_api.dylib"
            if dylib.exists():
                return dylib
    return None


def pick_dylib(app_id: int) -> Path | None:
    game_dylib = find_dylib_for_game(app_id)
    if game_dylib:
        return game_dylib
    if LOCAL_DYLIB.exists():
        return LOCAL_DYLIB
    setup_dylib()
    return LOCAL_DYLIB if LOCAL_DYLIB.exists() else None
