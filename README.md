![Steam Achievement Unlocker](image.png)

**CLI-инструмент** для просмотра и управления достижениями Steam на **macOS** (Intel и Apple Silicon).

- **Чтение:** Steam Web API (библиотека, ачивки, %)
- **Запись:** Steamworks (`libsteam_api.dylib`) через локальный клиент Steam

---

## Скачать

[![Download macOS](https://img.shields.io/badge/Download-macOS_.app-blue?style=for-the-badge&logo=apple&logoColor=white)](https://github.com/hellstation/steam-achievement-unlocker/releases/tag/v1.0.1)
[![Release v1.0.1](https://img.shields.io/badge/Release-v1.0.1-brightgreen?style=for-the-badge&logo=github)](https://github.com/hellstation/steam-achievement-unlocker/releases/tag/v1.0.1)

**[↓ Скачать Steam-Achievement-Unlocker-macOS.zip (v1.0.1)](https://github.com/hellstation/steam-achievement-unlocker/releases/download/v1.0.1/Steam-Achievement-Unlocker-macOS.zip)**

Все релизы: [Releases](https://github.com/hellstation/steam-achievement-unlocker/releases)

---

## Требования

- macOS
- Запущенный и авторизованный клиент Steam
- Steam Web API Key + SteamID64 (при первом запуске)
- **Из исходников:** Python 3.10+  
- **Из .app:** Python не нужен

---

## Запуск

### Вариант 1 — готовое приложение (.app)

1. Скачай zip с [релиза v1.0.1](https://github.com/hellstation/steam-achievement-unlocker/releases/tag/v1.0.1)  
   или напрямую:  
   [Steam-Achievement-Unlocker-macOS.zip](https://github.com/hellstation/steam-achievement-unlocker/releases/download/v1.0.1/Steam-Achievement-Unlocker-macOS.zip)
2. Распакуй архив
3. Перетащи `Steam Achievement Unlocker.app` в **Программы** (по желанию)
4. **Первый запуск:** ПКМ по приложению → **Открыть** (Gatekeeper)
5. Запусти **Steam** и войди в аккаунт
6. Открой приложение — запустится Terminal с меню

**Apple Silicon (M1/M2/M3):** приложение откроется нативно; внутри CLI идёт через **Rosetta**.  
Если Terminal напишет про Rosetta — один раз:

```bash
softwareupdate --install-rosetta --agree-to-license
```

`libsteam_api.dylib` при необходимости скачается в  
`~/Library/Application Support/SteamAchievementUnlocker/`

---

### Вариант 2 — из исходников (Terminal)

```bash
git clone https://github.com/hellstation/steam-achievement-unlocker.git
cd steam-achievement-unlocker
pip3 install -r requirements.txt
python3 main.py
```

> Зависимости (`requests`, `rich`) также ставятся автоматически при первом запуске, если их нет.

Дополнительные флаги:

```bash
python3 main.py --api-key <KEY> --steam-id <ID> --log-level INFO
STEAM_AUTO_REFRESH_SECONDS=60 python3 main.py
```

---

## Preflight

При старте проверяется:

- macOS
- Python 3.10+ (только при запуске из исходников)
- запущенный клиент Steam (иначе код выхода `7`)

Без Steam приложение сразу завершится.

`libsteam_api.dylib` нужна **только для записи** достижений.  
Просмотр библиотеки и списка ачивок возможен и без неё.

---

## Первый запуск (настройка)

**1. Steam Web API Key** — https://steamcommunity.com/dev/apikey (домен `localhost`)  
**2. SteamID64** — https://steamid.io (число вида `76561197989341403`)

Сохраняется в `~/.steam_ach_manager.json`  
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

Перед записью ачивок запрашивается подтверждение.

---

## Сборка .app у себя

```bash
bash scripts/build_macos_app.sh
```

Результат: `dist/Steam Achievement Unlocker.app`

---

## Структура

```
steam-achievement-unlocker/
├── main.py
├── requirements.txt
├── scripts/build_macos_app.sh
├── SteamAchievementUnlocker.spec
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

---

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
