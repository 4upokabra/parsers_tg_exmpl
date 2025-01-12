from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import asyncio
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')

# Инициализация Telegram бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Функция для получения новостей из базы данных
def get_news_from_db(offset=0, limit=10):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, date, content, link FROM news ORDER BY date DESC LIMIT ? OFFSET ?', (limit, offset))
    news = cursor.fetchall()
    conn.close()
    return news

# Функция для сохранения chat_id в файл
def save_chat_id(chat_id):
    with open('chats.txt', 'a') as file:
        file.write(f"{chat_id}\n")

# Функция для получения всех chat_id из файла
def get_all_chat_ids():
    with open('chats.txt', 'r') as file:
        chat_ids = [line.strip() for line in file.readlines()]
    return chat_ids

# Функция для получения всех новостей из базы данных
def get_all_news_from_db():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, date, content, link FROM news ORDER BY date DESC')
    news = cursor.fetchall()
    conn.close()
    return news

# Функция для разбивки текста на части
def split_message(text, max_length=4096):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# Обработчик команды /start
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    chat_id = message.chat.id
    save_chat_id(chat_id)
    await message.reply("Привет! Используйте команду /list, чтобы увидеть последние новости.")

# Обработчик команды /list
@dp.message(Command("list"))
async def send_news(message: types.Message):
    news = get_news_from_db()
    if not news:
        await message.reply("Нет новостей.")
        return

    builder = InlineKeyboardBuilder()
    for news_id, title, date, content, link in news:
        builder.add(types.InlineKeyboardButton(text=title, callback_data=f"news_{news_id}"))

    builder.adjust(2)  # Кнопки будут выводиться по две в строке
    builder.row(types.InlineKeyboardButton(text="<-", callback_data="prev_0"),
                types.InlineKeyboardButton(text="->", callback_data="next_0"))

    await message.reply("Последние новости:", reply_markup=builder.as_markup())

# Обработчик нажатий на кнопки новостей
@dp.callback_query(lambda c: c.data.startswith('news_'))
async def process_news_button(callback_query: types.CallbackQuery):
    news_id = int(callback_query.data.split('_')[1])
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT title, date, content, link FROM news WHERE id = ?', (news_id,))
    news = cursor.fetchone()
    conn.close()

    if news:
        title, date, content, link = news
        message = f"Заголовок: {title}\nДата и время: {date}\nТекст: {content}\nСсылка: {link}"
        message_parts = split_message(message)
        for part in message_parts:
            await bot.send_message(chat_id=callback_query.message.chat.id, text=part)
    else:
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Новость не найдена.")

    await callback_query.answer()

# Обработчик нажатий на кнопки навигации
@dp.callback_query(lambda c: c.data.startswith('prev_') or c.data.startswith('next_'))
async def process_navigation_button(callback_query: types.CallbackQuery):
    action, current_page = callback_query.data.split('_')
    current_page = int(current_page)

    if action == 'prev':
        current_page -= 1
    elif action == 'next':
        current_page += 1

    offset = current_page * 10
    news = get_news_from_db(offset=offset)
    if not news:
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Нет новостей.")
        return

    builder = InlineKeyboardBuilder()
    for news_id, title, date, content, link in news:
        builder.add(types.InlineKeyboardButton(text=title, callback_data=f"news_{news_id}"))

    builder.adjust(2)  # Кнопки будут выводиться по две в строке
    builder.row(types.InlineKeyboardButton(text="<-", callback_data=f"prev_{current_page}"),
                types.InlineKeyboardButton(text="->", callback_data=f"next_{current_page}"))

    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=builder.as_markup())

    await callback_query.answer()

# Функция для проверки новых новостей и отправки их пользователям
async def check_and_send_new_news():
    initial_news = get_all_news_from_db()
    initial_news_ids = {news[0] for news in initial_news}

    while True:
        await asyncio.sleep(60)  # Ждем 1 минуту
        current_news = get_all_news_from_db()
        current_news_ids = {news[0] for news in current_news}

        new_news_ids = current_news_ids - initial_news_ids
        if new_news_ids:
            new_news = [news for news in current_news if news[0] in new_news_ids]
            chat_ids = get_all_chat_ids()
            for news_item in new_news:
                news_id, title, date, content, link = news_item
                message = f"Новая новость!\nЗаголовок: {title}\nДата и время: {date}\nТекст: {content}\nСсылка: {link}"
                message_parts = split_message(message)
                for chat_id in chat_ids:
                    for part in message_parts:
                        await bot.send_message(chat_id=chat_id, text=part)

            initial_news_ids.update(new_news_ids)

# Запуск бота
async def main():
    await dp.start_polling(bot)
    await check_and_send_new_news()

if __name__ == '__main__':
    asyncio.run(main())
