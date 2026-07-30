#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random
import requests
import threading
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ============================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER
# ============================================

@app.route('/')
def index():
    return '🕵️ SHERLOCK V2.0 работает 24/7!'

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ============================================
# SHERLOCK
# ============================================

def sherlock_search(query):
    login = f"demo_user_{random.randint(1000,9999)}"
    email = f"demo_{random.randint(100,999)}@example.com"
    password = f"Demo{random.randint(100,999)}"
    cities = ["Москва", "СПб", "Новосибирск", "Казань", "Екатеринбург"]
    
    return {
        'login': login,
        'email': email,
        'password': password,
        'city': random.choice(cities),
        'phone': query
    }

# ============================================
# MAP SEARCH
# ============================================

def search_address(query):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'accept-language': 'ru'
        }
        headers = {'User-Agent': 'sherlock_bot/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data:
            return {
                'address': data[0]['display_name'],
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon'])
            }
        return None
    except Exception as e:
        print(f"Ошибка карт: {e}")
        return None

def get_map_buttons(lat, lon):
    urls = {
        'yandex': f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map",
        '2gis': f"https://2gis.ru/geo/{lat},{lon}",
        'google': f"https://www.google.com/maps?q={lat},{lon}"
    }
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🗺️ Яндекс", url=urls['yandex']),
        InlineKeyboardButton("🗺️ 2ГИС", url=urls['2gis'])
    )
    keyboard.add(
        InlineKeyboardButton("🗺️ Google Maps", url=urls['google'])
    )
    return keyboard

# ============================================
# КОМАНДЫ
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🕵️ SHERLOCK V2.0\n\n"
        "Доступные режимы:\n\n"
        "1️⃣ SHERLOCK — поиск по номеру/почте\n"
        "   Пример: +79991234567\n\n"
        "2️⃣ MAP SEARCH — поиск адреса\n"
        "   Пример: Москва Кремль"
    )

@bot.message_handler(commands=['map'])
def map_command(message):
    query = message.text.replace('/map', '').strip()
    
    if not query:
        bot.reply_to(message, "📍 Укажите адрес: `/map Москва Кремль`")
        return
    
    bot.reply_to(message, f"🗺️ Ищу адрес: {query}...")
    time.sleep(1)
    
    result = search_address(query)
    
    if result:
        keyboard = get_map_buttons(result['lat'], result['lon'])
        reply = f"✅ НАЙДЕНО:\n\n📍 {result['address']}\n\n🗺️ {result['lat']}, {result['lon']}\n\nВыберите карту:"
        bot.reply_to(message, reply, reply_markup=keyboard)
    else:
        bot.reply_to(message, "❌ Адрес не найден")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    # MAP SEARCH
    if any(c.isalpha() for c in query) and len(query) > 5:
        bot.reply_to(message, f"🗺️ Ищу адрес: {query}...")
        time.sleep(1)
        
        result = search_address(query)
        
        if result:
            keyboard = get_map_buttons(result['lat'], result['lon'])
            reply = f"✅ НАЙДЕНО:\n\n📍 {result['address']}\n\n🗺️ {result['lat']}, {result['lon']}\n\nВыберите карту:"
            bot.reply_to(message, reply, reply_markup=keyboard)
            return
    
    # SHERLOCK
    if any(char.isdigit() for char in query) or '@' in query:
        bot.reply_to(message, f"🔍 SHERLOCK: ищу {query}...")
        time.sleep(1)
        
        data = sherlock_search(query)
        
        reply = (
            f"✅ РЕЗУЛЬТАТ SHERLOCK\n\n"
            f"📱 Запрос: {data['phone']}\n"
            f"👤 Логин: {data['login']}\n"
            f"📧 Почта: {data['email']}\n"
            f"🔑 Пароль: {data['password']}\n"
            f"📍 Город: {data['city']}\n\n"
            f"⚠️ Демо-данные!"
        )
        bot.reply_to(message, reply)
        return
    
    bot.reply_to(
        message,
        "❌ Я не понял.\n\n"
        "🔍 SHERLOCK: +79991234567 или test@mail.ru\n"
        "🗺️ MAP SEARCH: Москва Кремль"
    )

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    # Запускаем веб-сервер для Render
    threading.Thread(target=run_web, daemon=True).start()
    
    # Запускаем бота
    while True:
        try:
            print("🕵️ SHERLOCK V2.0 запущен!")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10)
