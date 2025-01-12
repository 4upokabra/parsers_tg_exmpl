import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest

# Загружаем переменные окружения из .env файла
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')

print(f'API_ID: {api_id}')
print(f'API_HASH: {api_hash}')
print(f'PHONE: {phone}')


# Проверяем, что переменные окружения загружены корректно
if not api_id or not api_hash or not phone:
    raise ValueError("API_ID, API_HASH, or PHONE is not set in the .env file.")

# Создаем клиент
client = TelegramClient('session_name', api_id, api_hash)

async def main():
    await client.start(phone)

    # Имя пользователя группы или канала
    username = 'wildberries_mplacechat'

    # Получаем информацию о группе или канале
    result = await client(ResolveUsernameRequest(username))

    # Выводим ID группы или канала
    chat_id = result.peer.channel_id if hasattr(result.peer, 'channel_id') else result.peer.chat_id
    print(f'ID группы или канала: {chat_id}')

with client:
    client.loop.run_until_complete(main())
