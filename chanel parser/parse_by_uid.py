import os
import sqlite3
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, MessageMediaPhoto, MessageMediaDocument

# Загружаем переменные окружения из .env файла
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')
chat_id = os.getenv('CHAT_ID')
target_user_id = int(os.getenv('TARGET_USER_ID'))  # ID пользователя, сообщения которого нужно собрать

# Создаем клиент
client = TelegramClient('session_name', api_id, api_hash)

# Функция для создания таблицы в базе данных
def create_table():
    conn = sqlite3.connect('telegram_messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            user_id INTEGER,
            message TEXT,
            media_type TEXT,
            media_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Функция для вставки сообщений в базу данных
def insert_messages(messages):
    conn = sqlite3.connect('telegram_messages.db')
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO messages (date, user_id, message, media_type, media_url) VALUES (?, ?, ?, ?, ?)
    ''', messages)
    conn.commit()
    conn.close()

async def main():
    await client.start(phone)

    # Если это канал, нужно использовать PeerChannel
    if chat_id.startswith('-100'):
        chat_entity = PeerChannel(int(chat_id[4:]))
    else:
        chat_entity = int(chat_id)

    offset_id = 0
    limit = 100  # Количество сообщений за один запрос
    all_messages = []
    batch_size = 10  # Количество сообщений для сохранения в базу данных
    total_processed = 0  # Общее количество обработанных сообщений
    now_parsed = 0  # Общее количество сообщений, которые были обработаны в прошлом запросе
    # Создаем таблицу в базе данных
    create_table()

    while True:
        history = await client(GetHistoryRequest(
            peer=chat_entity,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        now_parsed = now_parsed + len(history.messages)
        if not history.messages:
            break

        messages = history.messages
        for message in messages:
            if message.sender_id == target_user_id:
                media_type = None
                media_url = None

                if message.media:
                    if isinstance(message.media, MessageMediaPhoto):
                        media_type = 'photo'
                        media_url = f"https://t.me/{chat_id}/{message.id}"
                    elif isinstance(message.media, MessageMediaDocument):
                        media_type = 'document'
                        media_url = f"https://t.me/{chat_id}/{message.id}"

                all_messages.append((message.date.strftime('%Y-%m-%d %H:%M:%S'), message.sender_id, message.message, media_type, media_url))
                total_processed += 1

        offset_id = messages[-1].id
        print(f'Parsed {total_processed} messages from the target user so far...')
        print(f'Parsed {now_parsed} messages from the target user in the last request...')
        # Если количество сообщений достигло batch_size, сохраняем их в базу данных
        if len(all_messages) >= batch_size:
            insert_messages(all_messages)
            print(f"Saved {len(all_messages)} messages to the database")
            all_messages = []  # Очищаем список сообщений

    # Сохраняем оставшиеся сообщения, если они есть
    if all_messages:
        insert_messages(all_messages)
        print(f"Saved remaining {len(all_messages)} messages to the database")

with client:
    client.loop.run_until_complete(main())
