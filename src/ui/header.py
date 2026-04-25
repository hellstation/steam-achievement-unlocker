from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.prompt import Prompt

console = Console()


def print_header():
    console.print(Panel(
        "[bold white]Steam Achievement Unlocker[/bold white] [dim]— macOS CLI[/dim]\n"
        "[dim]Intel & Apple Silicon · sqwrtick[/dim]",
        style="on #1b2838",
        padding=(0, 2)
    ))
    console.print()


def first_run_wizard() -> tuple:
    console.print(Rule("[bold]Первый запуск — настройка[/bold]"))
    console.print()
    console.print(Panel(
        "Для работы нужны два параметра:\n\n"
        "[bold cyan]1. Steam Web API Key[/bold cyan]\n"
        "   Перейдите на [link=https://steamcommunity.com/dev/apikey]https://steamcommunity.com/dev/apikey[/link]\n"
        "   Введите любой домен (например [dim]localhost[/dim]) и нажмите «Согласен»\n"
        "   Скопируйте ключ вида [dim]CDBA2144766FAB60E55C4288A64C4EE4[/dim]\n\n"
        "[bold cyan]2. SteamID64[/bold cyan]\n"
        "   Перейдите на [link=https://steamid.io]https://steamid.io[/link] и вставьте URL вашего профиля\n"
        "   Нужно число вида [dim]76561197989341403[/dim]\n\n"
        "[dim]Данные сохранятся локально (~/.steam_ach_manager.json)[/dim]\n"
        "[dim]При следующем запуске вводить не нужно[/dim]",
        title="[bold]Добро пожаловать![/bold]",
        style="cyan",
        padding=(1, 2)
    ))
    console.print()

    api_key  = Prompt.ask("[bold]Steam Web API Key[/bold]")
    steam_id = Prompt.ask("[bold]SteamID64[/bold]")

    return api_key.strip(), steam_id.strip()
