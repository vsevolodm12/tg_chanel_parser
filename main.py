import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from telegram.ext import Application

from database.db import init_db, is_post_processed, add_processed_post, mark_as_sent
from detectors.first_pass import quick_check
from detectors.second_pass import llm_detect
from processors.formatter import format_event_message
from tg_client.reader import init_client, fetch_new_posts
from tg_client.bot import init_bot, send_message
from bot_handler import setup_bot_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

CHANNELS_PATH = Path(__file__).resolve().parent / "channels.json"


def load_channels() -> List[str]:
    if not CHANNELS_PATH.exists():
        return []
    try:
        data = json.loads(CHANNELS_PATH.read_text(encoding="utf-8"))
        return [c.strip().lstrip("@") for c in data if c.strip()]
    except Exception:
        return []


async def process_channel(client, bot, channel: str) -> None:
    posts = await fetch_new_posts(client, channel, limit=10)
    logger.info("Канал %s: найдено %s новых постов", channel, len(posts))

    # Игнорируем посты старше 7 дней
    cutoff_date = datetime.now() - timedelta(days=7)
    
    for post in posts:
        post_id = post["id"]
        text = post["text"]
        date_str = post["date"]
        source_link = f"https://t.me/{channel}/{post_id}"

        if is_post_processed(channel, post_id):
            continue
        
        # Проверяем дату поста - игнорируем старые посты
        try:
            if isinstance(date_str, str):
                post_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                post_date = date_str
            if isinstance(post_date, datetime):
                # Убираем timezone для сравнения
                post_date_naive = post_date.replace(tzinfo=None) if post_date.tzinfo else post_date
                if post_date_naive < cutoff_date:
                    logger.info(f"Канал {channel}, пост {post_id}: пост слишком старый ({post_date_naive}), пропускаю")
                    add_processed_post(channel, post_id, date_str, text, False, {})
                    continue
        except Exception as e:
            logger.warning(f"Канал {channel}, пост {post_id}: не удалось распарсить дату {date_str}: {e}")
            # Продолжаем обработку, если не удалось распарсить дату

        if not quick_check(text):
            logger.info(f"Канал {channel}, пост {post_id}: не прошёл first_pass (быстрая проверка)")
            add_processed_post(channel, post_id, date_str, text, False, {})
            continue

        logger.info(f"Канал {channel}, пост {post_id}: прошёл first_pass, вызываю LLM...")
        result = llm_detect(text)
        is_event = bool(result.get("is_event"))
        add_processed_post(channel, post_id, date_str, text, is_event, result)

        if is_event:
            # Проверяем, что есть хотя бы какая-то полезная информация
            # Если все поля пустые (null), то это не полноценное событие (например, дайджест)
            has_useful_data = any([
                result.get("title"),
                result.get("date"),
                result.get("place"),
                result.get("link"),
                result.get("description")
            ])
            
            if has_useful_data:
                message = format_event_message(result, source_link)
                await send_message(bot, message)
                mark_as_sent(channel, post_id)
            else:
                logger.info(f"Канал {channel}, пост {post_id}: событие без полезных данных (дайджест?), пропускаю отправку в бот")
                # Не отправляем, но помечаем как обработанное


async def worker():
    # Приоритет: POLL_INTERVAL_SECONDS (для тестов), иначе POLL_INTERVAL_MINUTES
    poll_interval_env = os.getenv("POLL_INTERVAL_SECONDS")
    if poll_interval_env:
        poll_interval_seconds = float(poll_interval_env)
    else:
        poll_interval_minutes = float(os.getenv("POLL_INTERVAL_MINUTES", "30"))
        poll_interval_seconds = poll_interval_minutes * 60
    channels = load_channels()
    if not channels:
        logger.warning("Нет каналов в channels.json")

    client = await init_client()
    logger.info("Telethon клиент подключен")
    
    # Создаем Application для обработки команд бота
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if bot_token:
        application = Application.builder().token(bot_token).build()
        setup_bot_handlers(application)
        
        # Запускаем бота для обработки команд в отдельном потоке
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                application.run_polling(drop_pending_updates=True, stop_signals=None)
            except Exception as e:
                logger.error(f"Ошибка в боте: {e}", exc_info=True)
            finally:
                loop.close()
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Бот запущен для обработки команд")
    
    # Создаем простой Bot для отправки сообщений (для обратной совместимости)
    bot = init_bot()
    logger.info("Сервис запущен, начинаю обработку каналов...")

    while True:
        try:
            for channel in channels:
                await process_channel(client, bot, channel)
        except Exception as exc:
            logger.exception("Ошибка цикла: %s", exc)
        await asyncio.sleep(poll_interval_seconds)


def main():
    # Загружаем .env; если нет, пробуем env.sample
    env_loaded = load_dotenv()
    if not env_loaded:
        load_dotenv("env.sample")
    init_db()
    asyncio.run(worker())


if __name__ == "__main__":
    main()

