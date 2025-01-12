import asyncio
import subprocess
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')

async def run_bot():
    from bot import main as bot_main
    await bot_main()

async def run_parser():
    while True:
        # Запуск парсера
        subprocess.run(["python", "pars.py"])
        # Ожидание 10 минут
        await asyncio.sleep(600)

async def main():
    # Запуск бота и парсера в отдельных задачах
    bot_task = asyncio.create_task(run_bot())
    parser_task = asyncio.create_task(run_parser())

    # Ожидание завершения задач
    await asyncio.gather(bot_task, parser_task)

if __name__ == '__main__':
    asyncio.run(main())
