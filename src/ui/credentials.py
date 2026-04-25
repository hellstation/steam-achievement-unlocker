from rich.console import Console
from rich.prompt import Confirm

from ..config import load_config, save_config
from ..api.steam_web_api import SteamWebAPI
from ..errors import ConfigError
from .header import first_run_wizard

console = Console()


def _is_valid_api_key(value: str) -> bool:
    return len(value) == 32 and all(c in "0123456789abcdefABCDEF" for c in value)


def _is_valid_steam_id(value: str) -> bool:
    return value.isdigit() and len(value) == 17


def setup_credentials(
    api_key_override: str | None = None,
    steam_id_override: str | None = None,
    non_interactive: bool = False,
) -> tuple[str, str]:
    if api_key_override is not None or steam_id_override is not None:
        api_key = (api_key_override or "").strip()
        steam_id = (steam_id_override or "").strip()
        if not _is_valid_api_key(api_key):
            raise ConfigError("Некорректный API Key: ожидается 32 hex-символа")
        if not _is_valid_steam_id(steam_id):
            raise ConfigError("Некорректный SteamID64: ожидается 17 цифр")
        save_config({"api_key": api_key, "steam_id": steam_id})
        return api_key, steam_id

    cfg      = load_config()
    api_key  = cfg.get("api_key", "")
    steam_id = cfg.get("steam_id", "")

    if non_interactive and (not _is_valid_api_key(api_key) or not _is_valid_steam_id(steam_id)):
        raise ConfigError("В non-interactive режиме укажите --api-key и --steam-id или сохраните валидные данные в конфиге")

    if not api_key or not steam_id or not _is_valid_api_key(api_key) or not _is_valid_steam_id(steam_id):
        if api_key or steam_id:
            console.print("[yellow]Сохранённые API Key/SteamID выглядят некорректно, введите их заново.[/yellow]")
        api_key, steam_id = first_run_wizard()
        while not _is_valid_api_key(api_key) or not _is_valid_steam_id(steam_id):
            console.print("[red]Проверьте формат: API Key = 32 hex-символа, SteamID64 = 17 цифр.[/red]")
            api_key, steam_id = first_run_wizard()
        save_config({"api_key": api_key, "steam_id": steam_id})
        return api_key, steam_id

    console.print(
        f"[dim]Аккаунт: SteamID [bold]···{steam_id[-6:]}[/bold] "
        f"· API Key [bold]···{api_key[-4:]}[/bold][/dim]"
    )
    if Confirm.ask("Сменить аккаунт?", default=False):
        api_key, steam_id = first_run_wizard()
        while not _is_valid_api_key(api_key) or not _is_valid_steam_id(steam_id):
            console.print("[red]Проверьте формат: API Key = 32 hex-символа, SteamID64 = 17 цифр.[/red]")
            api_key, steam_id = first_run_wizard()
        save_config({"api_key": api_key, "steam_id": steam_id})

    return api_key, steam_id


def show_profile(api: SteamWebAPI) -> dict:
    with console.status("Загрузка профиля..."):
        info = api.get_player_summary()
    if info:
        name = info.get("personaname", "Неизвестно")
        status_map = {0: "Оффлайн", 1: "В сети", 2: "Занят", 3: "Отошёл",
                      4: "Дремлю", 5: "Хочу играть", 6: "Хочу торговать"}
        status = status_map.get(info.get("personastate", 0), "?")
        console.print(f"[bold green]✓[/bold green] Профиль: [bold]{name}[/bold] [{status}]")
    else:
        console.print("[yellow]⚠ Не удалось загрузить профиль[/yellow]")
    return info
