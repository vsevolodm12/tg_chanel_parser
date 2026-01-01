#!/usr/bin/env python3
"""Скрипт для одноразовой авторизации Telethon"""
import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# Загружаем .env или env.sample
if os.path.exists('.env'):
    load_dotenv('.env')
else:
    load_dotenv('env.sample')

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    phone = os.getenv("TELEGRAM_PHONE", "")
    
    if not api_id or not api_hash or not phone:
        print("❌ Заполните TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE в .env")
        return
    
    client = TelegramClient("tg_session", api_id, api_hash)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"📱 Отправляю код на номер {phone}...")
            await client.send_code_request(phone)
            code = input("📨 Введите код из Telegram: ")
            
            try:
                await client.sign_in(phone=phone, code=code)
                print("✅ Авторизация успешна!")
            except Exception as e:
                if "SESSION_PASSWORD_NEEDED" in str(e):
                    password = input("🔐 Введите пароль 2FA: ")
                    await client.sign_in(password=password)
                    print("✅ Авторизация успешна (с 2FA)!")
                else:
                    print(f"❌ Ошибка: {e}")
                    return
        else:
            print("✅ Уже авторизован, сессия валидна!")
        
        # Проверяем что можем делать запросы
        me = await client.get_me()
        print(f"👤 Авторизован как: {me.first_name} (@{me.username or 'без username'})")
        
    finally:
        await client.disconnect()
        print("💾 Сессия сохранена в tg_session.session")

if __name__ == "__main__":
    asyncio.run(main())

