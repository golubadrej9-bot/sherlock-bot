#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# РЕЖИМ 1: SHERLOCK (поиск по номеру/почте)
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
# РЕЖИМ 2: MAP SEARCH (поиск адреса)
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

def get_map_urls(lat, lon, address):
    """Возвращает ссылки на все карты"""
    return {
        'yandex': f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map",
        '2gis': f"https://2gis.ru/geo/{lat},{lon}",
        'google': f"https://www.google.com/maps?q={lat},{lon}"
    }

def get_map_buttons(lat, lon, address):
    """Кнопки с картами"""
    urls = get_map_urls(lat, lon, address)
    
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
# КОМАНДЫ БОТА
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
        "   Пример: Москва Кремль\n\n"
        "3️⃣ /map [адрес] — открыть карту\n"
        "   Пример: /map Красная площадь"
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
        keyboard = get_map_buttons(result['lat'], result['lon'], result['address'])
        
        reply = (
            f"✅ НАЙДЕНО:\n\n"
            f"📍 {result['address']}\n\n"
            f"🗺️ Координаты:\n"
            f"   {result['lat']}, {result['lon']}\n\n"
            f"Выберите карту:"
        )
        bot.reply_to(message, reply, reply_markup=keyboard)
    else:
        bot.reply_to(message, "❌ Адрес не найден")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    # ===== MAP SEARCH (адрес) =====
    if any(c.isalpha() for c in query) and len(query) > 5:
        bot.reply_to(message, f"🗺️ Ищу адрес: {query}...")
        time.sleep(1)
        
        result = search_address(query)
        
        if result:
            keyboard = get_map_buttons(result['lat'], result['lon'], result['address'])
            
            reply = (
                f"✅ НАЙДЕНО:\n\n"
                f"📍 {result['address']}\n\n"
                f"🗺️ Координаты:\n"
                f"   {result['lat']}, {result['lon']}\n\n"
                f"Выберите карту:"
            )
            bot.reply_to(message, reply, reply_markup=keyboard)
            return
    
    # ===== SHERLOCK (номер/почта) =====
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
    
    # Если ничего не подошло
    bot.reply_to(
        message,
        "❌ Я не понял.\n\n"
        "🔍 SHERLOCK: +79991234567 или test@mail.ru\n"
        "🗺️ MAP SEARCH: Москва Кремль\n"
        "📌 /map [адрес]"
    )

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    while True:
        try:
            print("🕵️ SHERLOCK V2.0 запущен!")
            print("  1️⃣ SHERLOCK — поиск по номеру/почте")
            print("  2️⃣ MAP SEARCH — поиск адреса (Яндекс/2ГИС/Google)")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10)
