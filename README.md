![Steam Achievement Unlocker](image.png)

**CLI-инструмент** для просмотра и управления достижениями Steam на **macOS** (Intel и Apple Silicon).

- **Чтение:** Steam Web API (библиотека, ачивки, %)
- **Запись:** Steamworks (`libsteam_api.dylib`) через локальный клиент Steam

---

## Требования

- macOS
- Python 3.10 или новее
- Запущенный и авторизованный клиент Steam
- Steam Web API Key + SteamID64 (при первом запуске)

---

## Preflight

При старте скрипт проверяет:

- macOS
- Python 3.10+
- запущенный клиент Steam (иначе код выхода `7`)

Без запущенного Steam приложение сразу завершится.

`libsteam_api.dylib` нужна **только для записи** достижений.  
Просмотр библиотеки и списка ачивок возможен и без неё (запись откажет с понятной ошибкой).

---

## Установка

```bash
git clone https://github.com/hellstation/steam-achievement-unlocker.git
cd steam-achievement-unlocker
pip3 install -r requirements.txt
```

> Зависимости (`requests`, `rich`) также ставятся автоматически при первом запуске, если их нет.

---

## Запуск

```bash
python3 main.py
```

---

## Первый запуск

**1. Steam Web API Key** — https://steamcommunity.com/dev/apikey (домен `localhost`)  
**2. SteamID64** — https://steamid.io (число вида `76561197989341403`)

Данные: `~/.steam_ach_manager.json`  
Кэш игр: `~/.steam_ach_manager_games_cache.json`

---

## Использование

1. Поиск игры или Enter — полный список  
2. Выбор по номеру  
3. Действия:
   - `1` / `2` — unlock / lock **все**
   - `3` / `4` — unlock / lock **конкретное**
   - `5` — обновить с сервера
   - `0` — назад

```bash
STEAM_AUTO_REFRESH_SECONDS=60 python3 main.py
python3 main.py --api-key <KEY> --steam-id <ID> --log-level INFO
```

---

## Структура

```
steam-achievement-unlocker/
├── main.py
├── requirements.txt
├── tests/
└── src/
    ├── preflight.py
    ├── config.py
    ├── constants.py
    ├── errors.py
    ├── exit_codes.py
    ├── logging_utils.py
    ├── api/steam_web_api.py
    ├── steamworks/
    │   ├── ctypes_wrapper.py
    │   └── dylib_manager.py
    └── ui/
```

---

## Логи

`~/.steam_ach_manager.log` (JSON)

---

## Тесты

```bash
python3 -m pip install pytest
python3 -m pytest
```

## Коды выхода

| Код | Значение |
|-----|----------|
| `0` | Успех |
| `2` | Авторизация |
| `3` | Приватность |
| `4` | Сеть |
| `5` | Конфиг / ОС / Python |
| `6` | Ответ API |
| `7` | Steam не запущен |
