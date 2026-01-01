import os
from datetime import datetime
from typing import List, Dict, Any

from telethon import TelegramClient
from telethon.tl.types import Message

from database.db import is_post_processed


SESSION_NAME = "tg_session"


async def init_client() -> TelegramClient:
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    phone = os.getenv("TELEGRAM_PHONE", "")
    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await client.start(phone=phone)
    return client


def _message_to_dict(msg: Message) -> Dict[str, Any]:
    return {
        "id": msg.id,
        "text": msg.message or "",
        "date": msg.date.isoformat() if isinstance(msg.date, datetime) else str(msg.date),
    }


async def fetch_new_posts(client: TelegramClient, channel_username: str, limit: int = 50) -> List[Dict[str, Any]]:
    posts: List[Dict[str, Any]] = []
    async for msg in client.iter_messages(channel_username, limit=limit):
        if not msg.message:
            continue
        if is_post_processed(channel_username, msg.id):
            continue
        posts.append(_message_to_dict(msg))
    return list(reversed(posts))

