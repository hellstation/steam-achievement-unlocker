import time
import logging

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..api.steam_web_api import SteamWebAPI
from ..steamworks.ctypes_wrapper import SteamworksCtypes
from ..steamworks.dylib_manager import pick_dylib
from .game_selector import load_game_achievements

console = Console()
logger = logging.getLogger("steam_unlick.ui.achievement_menu")


def show_achievements(achievements: list, game_name: str):
    unlocked = sum(1 for a in achievements if a["unlocked"])
    total    = len(achievements)
    pct      = round(unlocked / total * 100) if total else 0

    console.print(f"\n[bold]{game_name}[/bold] — {unlocked}/{total} достижений ({pct}%)")
    bar_len = 40
    filled  = int(bar_len * unlocked / total) if total else 0
    console.print("[green]" + "█" * filled + "[/green]" + "[dim]" + "░" * (bar_len - filled) + "[/dim]")

    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("#",           style="dim", width=4)
    table.add_column("Ст.",         width=4)
    table.add_column("Достижение",  min_width=28)
    table.add_column("Описание",    min_width=30)
    table.add_column("%игр",        justify="right", width=6)
    table.add_column("Дата",        width=12)

    for i, a in enumerate(achievements, 1):
        status = "[green]✓[/green]" if a["unlocked"] else "[dim]○[/dim]"
        desc   = ("[dim italic]Скрытое[/dim italic]"
                  if a["hidden"] and not a["unlocked"]
                  else a["desc"][:40] + ("…" if len(a["desc"]) > 40 else ""))

        pct_str = f"{a['global_pct']:.1f}%" if a["global_pct"] else "?"
        if   a["global_pct"] and a["global_pct"] < 5:  pct_str = f"[red]{pct_str}[/red]"
        elif a["global_pct"] and a["global_pct"] < 15: pct_str = f"[yellow]{pct_str}[/yellow]"

        date_str = (time.strftime("%d.%m.%Y", time.localtime(a["unlock_time"]))
                    if a["unlocked"] and a["unlock_time"] else "")

        table.add_row(str(i), status, a["name"], desc, pct_str, date_str)

    console.print(table)


def apply_achievements(api: SteamWebAPI, game: dict, achievements: list, action: str):
    app_id = game["appid"]

    if action == "1":
        targets = [a for a in achievements if not a["unlocked"]]
        unlock, label = True,  "разблокировать все"
    elif action == "2":
        targets = [a for a in achievements if a["unlocked"]]
        unlock, label = False, "заблокировать все"
    elif action == "3":
        idx = Prompt.ask("Номер достижения")
        try:
            a = achievements[int(idx) - 1]
            targets, unlock, label = [a], True, f"разблокировать «{a['name']}»"
        except (ValueError, IndexError):
            console.print("[red]Неверный номер[/red]"); return
    elif action == "4":
        idx = Prompt.ask("Номер достижения")
        try:
            a = achievements[int(idx) - 1]
            targets, unlock, label = [a], False, f"заблокировать «{a['name']}»"
        except (ValueError, IndexError):
            console.print("[red]Неверный номер[/red]"); return
    else:
        return

    if not targets:
        logger.info("apply_achievements_noop", extra={"app_id": app_id, "action": action})
        console.print("[yellow]Нечего менять — все уже в нужном статусе[/yellow]")
        return

    console.print(f"\n[yellow]Действие: {label} ({len(targets)} шт.)[/yellow]")
    console.print("[bold red]⚠  Это изменит данные на серверах Steam![/bold red]")
    if not Confirm.ask("Продолжить?", default=False):
        logger.info("apply_achievements_cancelled_by_user", extra={"app_id": app_id, "action": action, "target_count": len(targets)})
        console.print("[dim]Отменено.[/dim]"); return

    dylib = pick_dylib(app_id)
    if not dylib:
        logger.error("apply_achievements_no_dylib", extra={"app_id": app_id})
        console.print("[red]Отмена — библиотека недоступна[/red]"); return

    sw = SteamworksCtypes()
    console.print(f"\n[dim]Инициализация Steamworks (AppID {app_id})...[/dim]")
    ok, info = sw.init(app_id, dylib)

    if not ok:
        logger.error("apply_achievements_steamworks_init_failed", extra={"app_id": app_id, "dylib": str(dylib), "info": info})
        console.print(f"[red]✗ Ошибка:[/red]\n{info}"); return

    logger.info("apply_achievements_started", extra={"app_id": app_id, "action": action, "target_count": len(targets), "dylib": str(dylib)})
    console.print(f"[green]✓ Steamworks подключён[/green] ({dylib.name})\n")

    success, failed, failed_names = 0, 0, []

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  BarColumn(), TextColumn("{task.completed}/{task.total}")) as p:
        verb = "Разблокировка" if unlock else "Сброс"
        task = p.add_task(f"{verb}...", total=len(targets))
        for a in targets:
            res = sw.set_achievement(a["id"]) if unlock else sw.clear_achievement(a["id"])
            if res:
                a["unlocked"]    = unlock
                a["unlock_time"] = int(time.time()) if unlock else 0
                success += 1
            else:
                failed += 1
                failed_names.append(a["name"])
            p.advance(task)
            time.sleep(0.03)

    console.print("\n[dim]Сохранение на серверы Steam...[/dim]")
    stored = sw.store_stats()
    sw.shutdown()
    logger.info(
        "apply_achievements_finished",
        extra={"app_id": app_id, "action": action, "success": success, "failed": failed, "store_stats": bool(stored)},
    )

    console.print()
    if stored:
        console.print("[bold green]✓ Изменения сохранены в Steam![/bold green]")
    else:
        console.print("[yellow]⚠ StoreStats вернул false — обновите список (5)[/yellow]")

    if success: console.print(f"[green]✓ Успешно: {success}[/green]")
    if failed:
        console.print(f"[red]✗ Ошибок: {failed}[/red]")
        for n in failed_names[:5]:
            console.print(f"  [dim]- {n}[/dim]")


def achievement_menu(api: SteamWebAPI, game: dict, achievements: list):
    name = game.get("name", str(game["appid"]))
    while True:
        show_achievements(achievements, name)
        console.print("\n[bold]Действия:[/bold]")
        console.print("  [cyan]1[/cyan] — Разблокировать ВСЕ достижения")
        console.print("  [cyan]2[/cyan] — Заблокировать ВСЕ достижения")
        console.print("  [cyan]3[/cyan] — Разблокировать конкретное")
        console.print("  [cyan]4[/cyan] — Заблокировать конкретное")
        console.print("  [cyan]5[/cyan] — Обновить список с сервера")
        console.print("  [cyan]0[/cyan] — Назад к выбору игры")

        action = Prompt.ask("\nДействие")

        if action == "0":
            break
        elif action == "5":
            achievements.clear()
            achievements.extend(load_game_achievements(api, game))
        elif action in ("1", "2", "3", "4"):
            apply_achievements(api, game, achievements, action)
        else:
            console.print("[red]Неверный выбор[/red]")
