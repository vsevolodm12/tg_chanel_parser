# План реализации сервиса парсинга ТГ-каналов

## Технологический стек

- **Язык**: Python 3.10+
- **Telegram**: Telethon (чтение каналов)
- **LLM API**: polza.ai через OpenAI SDK
- **База данных**: SQLite (встроенный sqlite3)
- **Бот Telegram**: python-telegram-bot
- **Планировщик задач**: APScheduler

## Структура проекта

```
tgchanelparser/
├── .env                    # Переменные окружения (API ключи)
├── .gitignore             
├── requirements.txt        
├── channels.json           # Список каналов для парсинга
├── prompts/
│   └── event_detection.txt # Промпт для LLM (легко менять)
├── database/
│   ├── __init__.py
│   └── db.py              # Работа с SQLite
├── telegram/
│   ├── __init__.py
│   ├── reader.py          # Чтение каналов через Telethon
│   └── bot.py             # Отправка сообщений через бота
├── detectors/
│   ├── __init__.py
│   ├── first_pass.py      # Регексы + ключевые слова
│   └── second_pass.py     # LLM детект через polza.ai
├── processors/
│   ├── __init__.py
│   └── formatter.py       # Форматирование сообщения для бота
└── main.py                # Главный скрипт
```

## Файл channels.json

```json
[
  "channel1",
  "channel2",
  "channel3"
]
```

Просто массив строк с username каналов (без @).

## Файл prompts/event_detection.txt

```
Определи, является ли текст анонсом мероприятия (митап, конференция, лекция, воркшоп).

Текст: {text}

Верни ТОЛЬКО валидный JSON без дополнительного текста:
{
  "is_event": bool,
  "title": "string или null",
  "date": "string или null",
  "place": "string или null",
  "link": "string или null",
  "tags": ["string"] или []
}
```

Плейсхолдер `{text}` будет заменяться на реальный текст поста.

## Схема базы данных (SQLite)

```sql
-- Таблица для хранения обработанных постов
CREATE TABLE processed_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_username TEXT NOT NULL,
    post_id INTEGER NOT NULL,
    post_date TEXT NOT NULL,
    post_text TEXT,
    is_event INTEGER DEFAULT 0,
    extracted_data TEXT,  -- JSON строка
    processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    sent_to_bot INTEGER DEFAULT 0,
    UNIQUE(channel_username, post_id)
);

CREATE INDEX idx_processed_posts_channel_post ON processed_posts(channel_username, post_id);
```

## Пошаговый план реализации

### Шаг 1: Настройка проекта

1. **requirements.txt**:
```
telethon
openai
python-telegram-bot
APScheduler
python-dotenv
```

2. **.env**:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone
POLZA_AI_API_KEY=your_polza_api_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_CHAT_ID=your_chat_id
DATABASE_PATH=database.db
```

3. **.gitignore**:
```
*.db
*.session
.env
__pycache__/
venv/
*.pyc
```

4. **channels.json**:
```json
[]
```

5. **prompts/event_detection.txt** - создать файл с промптом (см. пример выше)

### Шаг 2: Модуль работы с БД (database/db.py)

- Функция `init_db()` — создание таблицы
- Функция `is_post_processed(channel_username, post_id)` → bool
- Функция `add_processed_post(channel_username, post_id, post_date, post_text, is_event, extracted_data)`
- Функция `mark_as_sent(channel_username, post_id)`

Использовать встроенный `sqlite3`, простые SQL запросы.

### Шаг 3: Модуль чтения каналов (telegram/reader.py)

- Функция `init_client()` — инициализация Telethon клиента
- Функция `fetch_new_posts(channel_username, limit=50)` → список постов
  - Каждый пост: `{id, text, date}`
  - Игнорирует уже обработанные (через БД)

### Шаг 4: Детектор событий

**detectors/first_pass.py**:
- Функция `quick_check(text)` → bool
- Ищет ключевые слова: ["митап", "конференция", "лекция", "воркшоп", "event", "meetup"]
- Простые регексы для дат и мест

**detectors/second_pass.py**:
- Функция `llm_detect(text)` → dict
- Читает промпт из `prompts/event_detection.txt`
- Заменяет `{text}` на реальный текст
- Вызывает polza.ai через OpenAI SDK
- Парсит JSON ответ, возвращает dict

### Шаг 5: Форматирование и отправка

**processors/formatter.py**:
- Функция `format_event_message(event_data, source_link)` → str
- Форматирует данные события:
```
🗓 {title}
📍 {place или "Уточняется"}
⏰ {date или "Уточняется"}
🏷 {tags через запятую или "нет"}
🔗 Регистрация: {link или "нет"}
🔗 Источник: {source_link}
```

**telegram/bot.py**:
- Функция `init_bot()` — инициализация бота
- Функция `send_message(text)` — отправка в чат

### Шаг 6: Главный скрипт (main.py)

1. Загрузить каналы из `channels.json`
2. Инициализировать БД (`init_db()`)
3. Инициализировать Telethon клиент
4. Инициализировать бота
5. Функция `process_channels()`:
   - Для каждого канала из JSON:
     - Получить новые посты
     - Для каждого поста:
       - Проверить, не обработан ли (БД)
       - First-pass проверка
       - Если проходит → Second-pass (LLM)
       - Если `is_event = True`:
         - Сохранить в БД
         - Отформатировать сообщение
         - Отправить в бота
         - Отметить как отправленное
6. Настроить APScheduler: запускать `process_channels()` каждые 30 минут

### Шаг 7: Логирование и ошибки

- Использовать `logging` модуль
- Логировать все этапы обработки
- Try-except для каждого канала (чтобы один сломанный не ломал весь процесс)
- Простой retry для LLM запросов (2-3 попытки)

## Порядок разработки

1. Настройка проекта (requirements.txt, .env, .gitignore)
2. Модуль БД (database/db.py)
3. Файлы конфигурации (channels.json, prompts/event_detection.txt)
4. Модуль чтения каналов (telegram/reader.py)
5. First-pass детектор (detectors/first_pass.py)
6. Second-pass детектор (detectors/second_pass.py)
7. Форматирование (processors/formatter.py)
8. Отправка через бота (telegram/bot.py)
9. Главный скрипт (main.py)
10. Тестирование

## Важные моменты

- **SQLite boolean**: Использует INTEGER (0 = False, 1 = True)
- **JSON в SQLite**: Хранить как TEXT, парсить через `json.loads()` / `json.dumps()`
- **Сессия Telethon**: Файл `.session` создается автоматически, не коммитить в git
- **Модель LLM**: Использовать `openai/gpt-4o-mini` для экономии
- **Дедупликация**: Проверять `(channel_username, post_id)` перед обработкой

## Пример подключения к SQLite

```python
import sqlite3
import os
import json

DB_PATH = os.getenv("DATABASE_PATH", "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_username TEXT NOT NULL,
            post_id INTEGER NOT NULL,
            post_date TEXT NOT NULL,
            post_text TEXT,
            is_event INTEGER DEFAULT 0,
            extracted_data TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            sent_to_bot INTEGER DEFAULT 0,
            UNIQUE(channel_username, post_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_processed_posts_channel_post 
        ON processed_posts(channel_username, post_id)
    """)
    conn.commit()
    conn.close()
```

## Пример использования polza.ai

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.polza.ai/api/v1",
    api_key=os.getenv("POLZA_AI_API_KEY"),
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Ты помощник для определения событий. Отвечай только JSON."},
        {"role": "user", "content": prompt_text}
    ],
    temperature=0.1,
    response_format={"type": "json_object"}
)
```
