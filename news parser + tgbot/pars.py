from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import sqlite3

# Настройка WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Открытие страницы
url = "https://metchel.gov74.ru/"
driver.get(url)

# Даем странице время для загрузки
time.sleep(5)

# Извлечение ссылок на новости
news_links = []

# Популярные новости
popular_news_elements = driver.find_elements(By.CSS_SELECTOR, ".big-news .text-news-title a")
for element in popular_news_elements:
    news_links.append(element.get_attribute('href'))

# Остальные новости
other_news_elements = driver.find_elements(By.CSS_SELECTOR, ".banner .item .item-title a")
for element in other_news_elements:
    news_links.append(element.get_attribute('href'))

# Подключение к базе данных SQLite
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

# Создание таблицы, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    date TEXT,
    link TEXT UNIQUE
)
''')

# Функция для извлечения данных из страницы новости
def extract_news_data(link):
    driver.get(link)
    time.sleep(3)  # Даем странице время для загрузки

    # Извлечение заголовка
    title = driver.find_element(By.CSS_SELECTOR, ".newsPage .aricle .item p").text

    # Извлечение полного текста новости
    content_elements = driver.find_elements(By.CSS_SELECTOR, ".newsPage .aricle .item p")
    content = "\n".join([element.text for element in content_elements])

    # Извлечение даты и времени
    date_element = driver.find_element(By.CSS_SELECTOR, ".pubDate")
    date = date_element.text.split('Дата публикации: ')[1].split('[')[0].strip()

    return title, content, date, link

# Извлечение данных из каждой новости и запись в базу данных
for link in news_links:
    try:
        # Проверка на дубликаты
        cursor.execute('SELECT 1 FROM news WHERE link = ?', (link,))
        if cursor.fetchone():
            print(f"Новость с ссылкой '{link}' уже существует в базе данных.")
            continue

        title, content, date, link = extract_news_data(link)
        cursor.execute('''
        INSERT INTO news (title, content, date, link)
        VALUES (?, ?, ?, ?)
        ''', (title, content, date, link))
        conn.commit()
        print(f"Новость '{title}' успешно добавлена в базу данных.")
    except Exception as e:
        print(f"Ошибка при извлечении данных из новости {link}: {e}")

# Закрытие браузера и базы данных
driver.quit()
conn.close()
