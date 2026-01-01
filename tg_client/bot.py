import os
from typing import Optional

from telegram import Bot


def init_bot() -> Bot:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    return Bot(token=token)


async def send_message(bot: Bot, text: str, chat_id: Optional[str] = None) -> None:
    target_chat = chat_id or os.getenv("TELEGRAM_BOT_CHAT_ID", "")
    if not target_chat:
        return
    await bot.send_message(chat_id=target_chat, text=text, disable_web_page_preview=True)

