import os
import logging
from typing import Optional, List

from telegram import Bot
from database.db import get_all_bot_users

logger = logging.getLogger(__name__)


def init_bot() -> Bot:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    return Bot(token=token)


async def send_message(bot: Bot, text: str, chat_id: Optional[str] = None) -> None:
    """Отправить сообщение конкретному пользователю или всем пользователям бота"""
    if chat_id:
        # Отправка конкретному пользователю
        try:
            await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")
        return
    
    # Отправка всем пользователям бота
    users = get_all_bot_users()
    
    # Если есть пользователи в БД, отправляем всем
    if users:
        for user in users:
            try:
                await bot.send_message(chat_id=user["chat_id"], text=text, disable_web_page_preview=True)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user['chat_id']}: {e}")
        logger.info(f"Сообщение отправлено {len(users)} пользователям")
    else:
        # Fallback: если нет пользователей в БД, отправляем в TELEGRAM_BOT_CHAT_ID
        fallback_chat = os.getenv("TELEGRAM_BOT_CHAT_ID", "")
        if fallback_chat:
            try:
                await bot.send_message(chat_id=fallback_chat, text=text, disable_web_page_preview=True)
                logger.info(f"Сообщение отправлено в fallback чат {fallback_chat}")
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения в fallback чат: {e}")

