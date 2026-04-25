import ctypes
import time
import logging
from pathlib import Path

from ..constants import SCRIPT_DIR

logger = logging.getLogger("steam_unlick.steamworks.ctypes")


class SteamworksCtypes:
    def __init__(self):
        self._lib         = None
        self._stats_iface = None
        self.initialized  = False
        self._appid_file  = SCRIPT_DIR / "steam_appid.txt"

    def init(self, app_id: int, dylib_path: Path) -> tuple:
        try:
            self._appid_file.write_text(str(app_id))
        except Exception as e:
            logger.exception("steamworks_write_appid_failed", extra={"app_id": app_id})
            return False, f"Не удалось записать steam_appid.txt: {e}"

        try:
            self._lib = ctypes.CDLL(str(dylib_path))
        except OSError as e:
            logger.exception("steamworks_load_dylib_failed", extra={"app_id": app_id, "dylib": str(dylib_path)})
            return False, f"Не удалось загрузить {dylib_path.name}: {e}"

        try:
            err_buf = ctypes.create_string_buffer(1024)
            init_fn = self._lib.SteamAPI_InitFlat
            init_fn.restype  = ctypes.c_int
            init_fn.argtypes = [ctypes.c_char_p]
            result = init_fn(err_buf)
            if result != 0:
                err_msg = err_buf.value.decode("utf-8", errors="replace")
                logger.error("steamworks_init_flat_error", extra={"app_id": app_id, "code": result, "error": err_msg})
                return False, (
                    f"SteamAPI_InitFlat вернул код {result}\n"
                    f"  Причина: {err_msg}\n"
                    "  • Убедитесь что Steam запущен и вы вошли в аккаунт\n"
                    f"  • Игра AppID {app_id} должна быть в вашей библиотеке"
                )
        except AttributeError:
            logger.error("steamworks_init_flat_not_found", extra={"app_id": app_id})
            return False, "SteamAPI_InitFlat не найдена в dylib"
        except Exception as e:
            logger.exception("steamworks_init_flat_failed", extra={"app_id": app_id})
            return False, f"Ошибка SteamAPI_InitFlat: {e}"

        self._stats_iface = None
        for ver in ("v013", "v012", "v011", "v010", "v009"):
            try:
                fn = getattr(self._lib, f"SteamAPI_SteamUserStats_{ver}")
                fn.restype  = ctypes.c_void_p
                fn.argtypes = []
                iface = fn()
                if iface:
                    self._stats_iface = iface
                    break
            except AttributeError:
                continue

        if not self._stats_iface:
            logger.error("steamworks_stats_interface_not_found", extra={"app_id": app_id})
            return False, "Не удалось получить интерфейс SteamUserStats"

        try:
            req = self._lib.SteamAPI_ISteamUserStats_RequestCurrentStats
            req.restype  = ctypes.c_bool
            req.argtypes = [ctypes.c_void_p]
            req(self._stats_iface)
            self._run_callbacks(1.0)
        except AttributeError:
            pass

        self.initialized = True
        logger.info("steamworks_init_ok", extra={"app_id": app_id, "dylib": str(dylib_path)})
        return True, str(dylib_path)

    def _run_callbacks(self, seconds: float = 0.1):
        try:
            run_cb = self._lib.SteamAPI_RunCallbacks
            run_cb.restype  = None
            run_cb.argtypes = []
            deadline = time.time() + seconds
            while time.time() < deadline:
                run_cb()
                time.sleep(0.01)
        except AttributeError:
            time.sleep(seconds)

    def set_achievement(self, api_name: str) -> bool:
        if not self.initialized:
            return False
        try:
            fn = self._lib.SteamAPI_ISteamUserStats_SetAchievement
            fn.restype  = ctypes.c_bool
            fn.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            return bool(fn(self._stats_iface, api_name.encode("utf-8")))
        except Exception:
            logger.exception("steamworks_set_achievement_failed", extra={"achievement_id": api_name})
            return False

    def clear_achievement(self, api_name: str) -> bool:
        if not self.initialized:
            return False
        try:
            fn = self._lib.SteamAPI_ISteamUserStats_ClearAchievement
            fn.restype  = ctypes.c_bool
            fn.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            return bool(fn(self._stats_iface, api_name.encode("utf-8")))
        except Exception:
            logger.exception("steamworks_clear_achievement_failed", extra={"achievement_id": api_name})
            return False

    def store_stats(self) -> bool:
        if not self.initialized:
            return False
        try:
            fn = self._lib.SteamAPI_ISteamUserStats_StoreStats
            fn.restype  = ctypes.c_bool
            fn.argtypes = [ctypes.c_void_p]
            result = bool(fn(self._stats_iface))
            self._run_callbacks(2.0)
            return result
        except Exception:
            logger.exception("steamworks_store_stats_failed")
            return False

    def shutdown(self):
        try:
            if self._lib:
                fn = self._lib.SteamAPI_Shutdown
                fn.restype  = None
                fn.argtypes = []
                fn()
        except Exception:
            logger.exception("steamworks_shutdown_failed")
            pass
        try:
            self._appid_file.unlink(missing_ok=True)
        except Exception:
            logger.exception("steamworks_remove_appid_failed")
            pass
        self.initialized = False
        self._lib = None
