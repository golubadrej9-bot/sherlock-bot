#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🕵️ SHERLOCK V2.0 работает 24/7 на Render!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    bot.reply_to(message, f"🔍 Ищу: {query}...")
    time.sleep(1)
    
    login = f"demo_user_{random.randint(1000,9999)}"
    email = f"demo_{random.randint(100,999)}@example.com"
    password = f"Demo{random.randint(100,999)}"
    
    bot.reply_to(
        message,
        f"✅ РЕЗУЛЬТАТ\n\n"
        f"👤 Логин: {login}\n"
        f"📧 Почта: {email}\n"
        f"🔑 Пароль: {password}\n\n"
        f"⚠️ Демо-данные!"
    )

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10)
