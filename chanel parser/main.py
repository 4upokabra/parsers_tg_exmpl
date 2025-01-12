import os
import sqlite3
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel

# Загружаем переменные окружения из .env файла
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')
chat_id = os.getenv('CHAT_ID')

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
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Функция для вставки сообщений в базу данных
def insert_messages(messages):
    conn = sqlite3.connect('telegram_messages.db')
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO messages (date, user_id, message) VALUES (?, ?, ?)
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
    batch_size = 500  # Количество сообщений для сохранения в базу данных

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

        if not history.messages:
            break

        messages = history.messages
        for message in messages:
            all_messages.append((message.date.strftime('%Y-%m-%d %H:%M:%S'), message.sender_id, message.message))

        offset_id = messages[-1].id
        print(f'Parsed {len(all_messages)} messages so far...')

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
