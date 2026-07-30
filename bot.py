#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random
import psycopg2

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# ============================================

DATABASE_URL = "postgresql://sherlock_user:oIWqt95Q6R3aQXekWuRT2ZjR1RBt0XUE@dpg-d91m15ijnfac73as0mtg-a:5432/sherlock_db_gcp5"

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return None

def init_database():
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        phone TEXT,
        email TEXT,
        name TEXT,
        age INTEGER,
        city TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS searches (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        query TEXT,
        result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    INSERT INTO users (phone, email, name, age, city)
    VALUES 
    ('+79001234567', 'ivanov@mail.ru', 'Иван Иванов', 30, 'Москва'),
    ('+79009876543', 'petrov@gmail.com', 'Петр Петров', 25, 'СПб'),
    ('+79005556677', 'sidorova@yandex.ru', 'Елена Сидорова', 22, 'Новосибирск')
    ON CONFLICT (id) DO NOTHING
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована!")

init_database()

def search_user(query):
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM users 
    WHERE phone LIKE %s 
       OR email LIKE %s 
       OR name LIKE %s
    LIMIT 5
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    results = cursor.fetchall()
    conn.close()
    return results

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🕵️ SHERLOCK V2.0\n\n"
        "Бот работает с базой данных!\n\n"
        "Отправь номер телефона, почту или имя.\n"
        "Пример: Иван Иванов"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    bot.reply_to(message, f"🔍 Ищу: {query}...")
    time.sleep(1)
    
    results = search_user(query)
    
    if results:
        reply = "✅ НАЙДЕНО:\n\n"
        for user in results:
            reply += f"👤 {user[3]}\n📱 {user[1]}\n📧 {user[2]}\n🎂 {user[4]} лет\n📍 {user[5]}\n\n"
    else:
        reply = "❌ Не найдено в базе\n\nДанные демонстрационные!"
    
    bot.reply_to(message, reply)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10)
