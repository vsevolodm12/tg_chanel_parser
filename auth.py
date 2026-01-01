from telethon import TelegramClient, errors
import os
import asyncio
from dotenv import load_dotenv

load_dotenv('.env')

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
session_name = 'tg_session'

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    try:
        await client.start()
        print("✅ Успех! Сессия создана.")
        me = await client.get_me()
        print(f"👤 Вы вошли как: {me.first_name}")
    except errors.SessionPasswordNeededError:
        password = input("🔐 Нужен пароль 2FA. Введите пароль: ")
        await client.sign_in(password=password)
        me = await client.get_me()
        print(f"✅ Авторизован как: {me.first_name}")
    except Exception as e:
        print(f"❌ Ошибка при входе: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
