import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database.db import get_last_events, add_bot_user
from processors.formatter import format_event_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    # Сохраняем пользователя в БД для рассылки уведомлений
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    add_bot_user(chat_id, username, first_name)
    logger.info(f"Пользователь добавлен/обновлен: chat_id={chat_id}, username={username}")
    
    keyboard = [[InlineKeyboardButton("📋 Посмотреть посты", callback_data="list_posts")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Йоу, блять! Я тот самый бот, который мониторит кучу Telegram каналов и ищет там мероприятия.\n\n"
        "🔔 Больше делать ничего не надо - уведомления о новых мероприятиях будут приходить сами!\n\n"
        "📋 А по кнопке ниже можешь посмотреть последние 5 постов.\n\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "list_posts":
        # Получаем последние 5 событий
        events = get_last_events(limit=5)
        
        if not events:
            await query.edit_message_text("Пока нет сохраненных событий.")
            return
        
        # Создаем кнопки с постами (используем индекс в списке)
        buttons = []
        for i, event in enumerate(events):
            # Ограничиваем длину названия для кнопки (макс 60 символов)
            title = event["title"][:57] + "..." if len(event["title"]) > 60 else event["title"]
            buttons.append([InlineKeyboardButton(
                f"{i+1}. {title}",
                callback_data=f"show_post_{i}"
            )])
        
        # Добавляем кнопку "Назад"
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            f"Выбери пост ({len(events)} доступно):",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("show_post_"):
        try:
            # Получаем индекс из callback_data
            index = int(query.data.split("_")[-1])
            
            # Получаем события из БД заново (чтобы гарантировать актуальность)
            events = get_last_events(limit=5)
            
            if 0 <= index < len(events):
                event = events[index]
                # Формируем ссылку и сообщение
                source_link = f"https://t.me/{event['channel']}/{event['post_id']}"
                message = format_event_message(event["data"], source_link)
                await query.edit_message_text(message, disable_web_page_preview=True)
            else:
                await query.edit_message_text("Пост не найден.")
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Ошибка парсинга callback_data: {query.data}, {e}")
            await query.edit_message_text("Ошибка: неверный формат данных")
    
    elif query.data == "back_to_start":
        # Возвращаемся к начальному экрану
        keyboard = [[InlineKeyboardButton("📋 Посмотреть посты", callback_data="list_posts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Йоу, блять! Я тот самый бот, который мониторит кучу Telegram каналов и ищет там мероприятия.\n\n"
            "Выбери действие:",
            reply_markup=reply_markup
        )


def setup_bot_handlers(application: Application) -> None:
    """Настройка обработчиков команд бота"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))

