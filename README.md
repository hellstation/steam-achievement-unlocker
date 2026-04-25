![kukokek](image.png)


**CLI-инструмент** для просмотра и управления достижениями Steam на macOS.  
Работает на Intel и Apple Silicon.

---

## Требования

- macOS
- Python 3.10 или новее
- Запущенный и авторизованный клиент Steam

---

## Установка

```bash
git clone https://github.com/hellstation/steam-achievement-unlocker.git
cd steam-achievement-unlocker
pip3 install -r requirements.txt
```

> Зависимости также устанавливаются автоматически при первом запуске.

---

## Запуск

```bash
python3 main.py
```

---

## Первый запуск

При первом запуске потребуются два параметра:

**1. Steam Web API Key**  
Перейдите на https://steamcommunity.com/dev/apikey, введите любой домен (например `localhost`) и скопируйте ключ.

**2. SteamID64**  
Перейдите на https://steamid.io, вставьте ссылку на профиль Steam и скопируйте число вида `73561097789349403`.

Данные сохраняются в `~/.steam_ach_manager.json` — при следующем запуске вводить не нужно.

---

## Использование

После запуска:

1. Введите название игры для поиска (или нажмите Enter для полного списка)
2. Выберите игру по номеру
3. Выберите действие:
   - `1` — разблокировать **все** достижения
   - `2` — заблокировать **все** достижения
   - `3` — разблокировать конкретное достижение
   - `4` — заблокировать конкретное достижение
   - `5` — обновить список достижений с сервера
   - `0` — вернуться к выбору игры
По умолчанию библиотека также автообновляется каждые `120` секунд.

Можно настроить интервал:

```bash
STEAM_AUTO_REFRESH_SECONDS=60 python3 main.py
```

Отключить автообновление:

```bash
STEAM_AUTO_REFRESH_SECONDS=0 python3 main.py
```

CLI-параметры:

```bash
python3 main.py --api-key <KEY> --steam-id <STEAM_ID> --auto-refresh 60 --log-level INFO
python3 main.py --non-interactive
```

Для `--non-interactive` скрипт загружает профиль/игры один раз и завершает работу с кодом выхода.

> **Примечание:** Steam API кэширует список игр на своих серверах. Если только что купленная игра не отображается, даже при автообновлении может потребоваться несколько минут/часов.

---

## Структура проекта

```
steam-achievement-unlocker/
├── main.py                       # точка входа
├── requirements.txt
└── src/
    ├── constants.py              # константы и пути
    ├── config.py                 # сохранение настроек
    ├── api/
    │   └── steam_web_api.py      # запросы к Steam Web API
    ├── steamworks/
    │   ├── ctypes_wrapper.py     # взаимодействие со Steamworks SDK
    │   └── dylib_manager.py      # поиск и загрузка libsteam_api.dylib
    └── ui/
        ├── header.py             # шапка и визард первого запуска
        ├── credentials.py        # управление учётными данными
        ├── game_selector.py      # выбор игры
        └── achievement_menu.py   # меню достижений
```

---

## Важно

Изменение достижений записывается напрямую на серверы Steam.  
Перед применением скрипт запрашивает подтверждение.

---

## Логи

Скрипт пишет структурированные JSON-логи в файл:

`~/.steam_ach_manager.log`

Там видны:
- ошибки запросов к Steam API;
- fallback на кэш библиотеки игр;
- причины пустых ответов (например, недоступные достижения);
- этапы Steamworks-инициализации и результат `StoreStats`.

---

## Тесты

```bash
python3 -m pip install pytest
python3 -m pytest
```
