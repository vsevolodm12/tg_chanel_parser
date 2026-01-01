# TG Channel Parser

Парсер Telegram каналов для автоматического поиска мероприятий с использованием LLM.

## Установка на сервер (одной командой)

```bash
curl -sSL https://raw.githubusercontent.com/vsevolodm12/tg_chanel_parser/main/install.sh | bash
```

Или через wget:
```bash
wget -qO- https://raw.githubusercontent.com/vsevolodm12/tg_chanel_parser/main/install.sh | bash
```

## После установки

1. **Перейдите в папку проекта:**
   ```bash
   cd ~/tg_chanel_parser
   ```

2. **Заполните .env файл:**
   ```bash
   nano .env
   ```
   
   Заполните:
   - `TELEGRAM_API_ID` — получить на https://my.telegram.org
   - `TELEGRAM_API_HASH` — получить там же
   - `TELEGRAM_PHONE` — ваш номер телефона (+79001234567)
   - `POLZA_AI_API_KEY` — API ключ от polza.ai
   - `TELEGRAM_BOT_TOKEN` — токен бота от @BotFather
   - `TELEGRAM_BOT_CHAT_ID` — ID чата для уведомлений

3. **Скопируйте сессию Telethon (если есть):**
   ```bash
   # На локальной машине:
   scp tg_session.session user@server:~/tg_chanel_parser/
   ```
   
   Или авторизуйтесь заново:
   ```bash
   source venv/bin/activate
   python3 auth.py
   ```

4. **Добавьте каналы для парсинга:**
   ```bash
   nano channels.json
   ```
   
   Формат:
   ```json
   [
     "channel1",
     "channel2"
   ]
   ```

5. **Запустите сервис:**
   ```bash
   bash start_service.sh
   ```

## Управление сервисом

```bash
bash start_service.sh   # Запуск
bash stop_service.sh    # Остановка
bash status_service.sh  # Статус
tail -f service.log     # Логи
```

## Настройка интервала опроса

В `.env`:
```
POLL_INTERVAL_MINUTES=30       # Интервал в минутах
# POLL_INTERVAL_SECONDS=1      # Для тестов (перекрывает минуты)
```

## Автозапуск через systemd

1. Отредактируйте `tgchanelparser.service`:
   - Замените `YOUR_USER` на вашего пользователя
   - Укажите правильный путь к проекту

2. Установите:
   ```bash
   sudo cp tgchanelparser.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable tgchanelparser
   sudo systemctl start tgchanelparser
   ```

## Структура проекта

```
tg_chanel_parser/
├── main.py              # Главный скрипт
├── auth.py              # Авторизация Telethon
├── channels.json        # Список каналов
├── prompts/             # Промпты для LLM
├── database/            # Работа с SQLite
├── detectors/           # Детекторы событий
├── processors/          # Форматирование
├── tg_client/           # Работа с Telegram
├── start_service.sh     # Запуск
├── stop_service.sh      # Остановка
└── status_service.sh    # Статус
```

