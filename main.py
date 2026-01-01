import asyncio
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv

from database.db import init_db, is_post_processed, add_processed_post, mark_as_sent
from detectors.first_pass import quick_check
from detectors.second_pass import llm_detect
from processors.formatter import format_event_message
from tg_client.reader import init_client, fetch_new_posts
from tg_client.bot import init_bot, send_message


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
    posts = await fetch_new_posts(client, channel, limit=50)
    logger.info("Канал %s: найдено %s новых постов", channel, len(posts))

    for post in posts:
        post_id = post["id"]
        text = post["text"]
        date = post["date"]
        source_link = f"https://t.me/{channel}/{post_id}"

        if is_post_processed(channel, post_id):
            continue

        if not quick_check(text):
            logger.info(f"Канал {channel}, пост {post_id}: не прошёл first_pass (быстрая проверка)")
            add_processed_post(channel, post_id, date, text, False, {})
            await send_message(bot, f"❌ Не событие\n🔗 {source_link}")
            continue

        logger.info(f"Канал {channel}, пост {post_id}: прошёл first_pass, вызываю LLM...")
        result = llm_detect(text)
        is_event = bool(result.get("is_event"))
        add_processed_post(channel, post_id, date, text, is_event, result)

        if is_event:
            message = format_event_message(result, source_link)
            await send_message(bot, message)
            mark_as_sent(channel, post_id)
        else:
            await send_message(bot, f"❌ Не событие\n🔗 {source_link}")


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
    bot = init_bot()

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

