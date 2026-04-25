import time
import logging

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..api.steam_web_api import SteamWebAPI

console = Console()
logger = logging.getLogger("steam_unlick.ui.game_selector")


def select_game(games: list) -> dict | None:
    if not games:
        console.print("[red]Нет игр в библиотеке[/red]")
        return None

    console.print(f"\n[bold]Ваша библиотека[/bold] [dim]({len(games)} игр)[/dim]")
    search = Prompt.ask("Поиск игры (или Enter для полного списка)", default="")

    filtered = games
    if search:
        filtered = [g for g in games if search.lower() in g.get("name", "").lower()]

    if not filtered:
        console.print("[yellow]Ничего не найдено[/yellow]")
        return None

    show = filtered[:30]
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("#",     style="dim", width=4)
    table.add_column("Игра",  min_width=30)
    table.add_column("Часов", justify="right", width=8)
    table.add_column("AppID", justify="right", style="dim", width=10)

    for i, g in enumerate(show, 1):
        hrs = round(g.get("playtime_forever", 0) / 60, 1)
        table.add_row(str(i), g.get("name", "?"), f"{hrs}ч", str(g.get("appid", "")))

    console.print(table)
    if len(filtered) > 30:
        console.print(f"[dim]... и ещё {len(filtered)-30}. Уточните поиск.[/dim]")

    choice = Prompt.ask(f"Выберите номер (1-{min(len(show), 30)})")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(show):
            return show[idx]
    except ValueError:
        pass

    console.print("[red]Неверный выбор[/red]")
    return None


def load_game_achievements(api: SteamWebAPI, game: dict) -> list:
    app_id = game["appid"]
    name   = game.get("name", str(app_id))
    started = time.time()

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as p:
        t = p.add_task(f"Загрузка достижений «{name}»...", total=3)
        schema      = api.get_schema(app_id);      p.advance(t)
        player_achs = api.get_player_achievements(app_id); p.advance(t)
        global_pct  = api.get_global_pct(app_id);  p.advance(t)

    if not schema:
        logger.warning("load_achievements_no_schema", extra={"app_id": app_id, "game_name": name})
        return []

    player_map = {a["apiname"]: a for a in player_achs}
    result = []
    for s in schema:
        pa = player_map.get(s["name"], {})
        result.append({
            "id":          s["name"],
            "name":        s.get("displayName") or s["name"],
            "desc":        s.get("description", "Описание скрыто"),
            "hidden":      bool(s.get("hidden", 0)),
            "unlocked":    pa.get("achieved", 0) == 1,
            "unlock_time": pa.get("unlocktime", 0),
            "global_pct":  float(global_pct.get(s["name"], 0.0)),
        })
    logger.info(
        "load_achievements_ok",
        extra={
            "app_id": app_id,
            "game_name": name,
            "schema_count": len(schema),
            "player_count": len(player_achs),
            "result_count": len(result),
            "duration_ms": int((time.time() - started) * 1000),
        },
    )
    return result
