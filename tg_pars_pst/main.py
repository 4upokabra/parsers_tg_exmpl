from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel

# Введите свои данные
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone_number = 'YOUR_PHONE_NUMBER'
channel_username = 'CHANNEL_USERNAME'  # Например, @example_channel
number_of_posts = 10  # Количество постов, которое вы хотите парсить

# Создаем клиент
client = TelegramClient('session_name', api_id, api_hash)

async def main():
    await client.start(phone_number)

    # Получаем информацию о канале
    channel = await client.get_entity(channel_username)

    # Получаем историю сообщений канала
    history = await client(GetHistoryRequest(
        peer=InputPeerChannel(channel.id, channel.access_hash),
        offset_id=0,
        offset_date=None,
        add_offset=0,
        limit=number_of_posts,
        max_id=0,
        min_id=0,
        hash=0
    ))

    # Выводим сообщения
    for message in history.messages:
        print(message.message)

with client:
    client.loop.run_until_complete(main())
