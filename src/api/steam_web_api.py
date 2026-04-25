import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..constants import STEAM_API_BASE
from ..errors import AuthError, NetworkError, APIResponseError

logger = logging.getLogger("steam_unlick.api")


class SteamWebAPI:
    def __init__(self, api_key: str, steam_id: str):
        self.api_key  = api_key
        self.steam_id = steam_id
        self._session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods={"GET"},
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def _get(self, url: str, params: dict = None) -> dict:
        p = {"key": self.api_key, "format": "json"}
        if params:
            p.update(params)
        try:
            r = self._session.get(url, params=p, timeout=15)
            r.raise_for_status()
            data = r.json()
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            logger.warning("steam_api_http_error", extra={"url": url, "status_code": code, "error": str(e)})
            if code in (401, 403):
                raise AuthError("Неверный API Key или недостаточно прав доступа") from e
            raise NetworkError(f"HTTP ошибка Steam API: {e}") from e
        except requests.RequestException as e:
            logger.warning("steam_api_request_failed", extra={"url": url, "error": str(e)})
            raise NetworkError(f"Сетевой запрос не удался: {e}") from e
        except ValueError as e:
            logger.warning("steam_api_invalid_json", extra={"url": url, "error": str(e)})
            raise APIResponseError("Steam API вернул некорректный JSON") from e

        if not isinstance(data, dict):
            logger.warning("steam_api_unexpected_payload_type", extra={"url": url, "payload_type": type(data).__name__})
            raise APIResponseError("Steam API вернул неожиданный формат ответа")
        return data

    def get_owned_games(self) -> list:
        data = self._get(
            f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v0001/",
            {"steamid": self.steam_id, "include_appinfo": "true",
             "include_played_free_games": "true"}
        )
        games = data.get("response", {}).get("games", [])
        if not isinstance(games, list):
            logger.warning("steam_api_owned_games_invalid_type", extra={"games_type": type(games).__name__})
            raise APIResponseError("GetOwnedGames вернул неожиданный формат поля games")
        logger.info("steam_api_owned_games_ok", extra={"count": len(games)})
        return sorted(games, key=lambda g: g.get("playtime_forever", 0), reverse=True)

    def get_player_achievements(self, app_id: int) -> list:
        try:
            data = self._get(
                f"{STEAM_API_BASE}/ISteamUserStats/GetPlayerAchievements/v0001/",
                {"appid": app_id, "steamid": self.steam_id, "l": "russian"}
            )
            return data.get("playerstats", {}).get("achievements", [])
        except Exception:
            logger.exception("steam_api_player_achievements_failed", extra={"app_id": app_id})
            return []

    def get_schema(self, app_id: int) -> list:
        try:
            data = self._get(
                f"{STEAM_API_BASE}/ISteamUserStats/GetSchemaForGame/v0002/",
                {"appid": app_id, "l": "russian"}
            )
            return data.get("game", {}).get("availableGameStats", {}).get("achievements", [])
        except Exception:
            logger.exception("steam_api_schema_failed", extra={"app_id": app_id})
            return []

    def get_global_pct(self, app_id: int) -> dict:
        try:
            data = self._get(
                f"{STEAM_API_BASE}/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/",
                {"gameid": app_id}
            )
            return {a["name"]: float(a["percent"])
                    for a in data.get("achievementpercentages", {}).get("achievements", [])}
        except Exception:
            logger.exception("steam_api_global_pct_failed", extra={"app_id": app_id})
            return {}

    def get_player_summary(self) -> dict:
        try:
            data = self._get(
                f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v0002/",
                {"steamids": self.steam_id}
            )
            players = data.get("response", {}).get("players", [])
            return players[0] if players else {}
        except Exception:
            logger.exception("steam_api_player_summary_failed")
            return {}
