#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

if os.path.exists('.env'):
    load_dotenv('.env')
else:
    load_dotenv('env.sample')

async def send_code():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")
    
    print(f"API ID: {api_id}")
    print(f"Phone: {phone}")
    print(f"API Hash: {api_hash[:10]}...")
    
    client = TelegramClient("tg_session", int(api_id), api_hash)
    
    try:
        await client.connect()
        print("Подключение установлено...")
        
        # Пробуем разные форматы номера
        phone_clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        print(f"Отправляю код на: {phone_clean}")
        
        result = await client.send_code_request(phone_clean)
        print(f"✅ Код отправлен! Phone code hash: {result.phone_code_hash[:10]}...")
        print("Проверь Telegram, должен прийти код.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(send_code())

