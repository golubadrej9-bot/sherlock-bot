#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random
import requests
import json
import os
import threading
from datetime import datetime
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return '🕵️ SHERLOCK V2.0 работает 24/7!'

def run_web():
    app.run(host='0.0.0.0', port=10000, debug=False)

# ============================================
# ФАЙЛЫ
# ============================================

DATA_FILE = "user_data.json"
PROMO_FILE = "promocodes.json"  # ВАШ ФАЙЛ

# ============================================
# ЗАГРУЗКА ПРОМОКОДОВ ИЗ ВАШЕГО ФАЙЛА
# ============================================

def load_promocodes():
    if os.path.exists(PROMO_FILE):
        with open(PROMO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_promocodes(promos):
    with open(PROMO_FILE, "w", encoding="utf-8") as f:
        json.dump(promos, f, ensure_ascii=False, indent=2)

# ============================================
# ПОЛЬЗОВАТЕЛИ
# ============================================

def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    data = load_user_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"requests": 1, "last_date": datetime.now().strftime("%Y-%m-%d"), "used_promos": []}
        save_user_data(data)
    return data[user_id]

def reset_requests_if_needed(user_id):
    user = get_user(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_date"] != today:
        user["requests"] = 1
        user["last_date"] = today
        save_user_data(load_user_data())
    return user

def use_request(user_id):
    user = reset_requests_if_needed(user_id)
    if user["requests"] > 0:
        user["requests"] -= 1
        save_user_data(load_user_data())
        return True
    return False

def get_remaining_requests(user_id):
    user = reset_requests_if_needed(user_id)
    return user["requests"]

def use_promocode(user_id, promo_code):
    user = get_user(user_id)
    promos = load_promocodes()
    
    if promo_code not in promos:
        return False, "❌ Неверный промокод"
    if promo_code in user["used_promos"]:
        return False, "❌ Уже использован"
    if promos[promo_code].get("used", False):
        return False, "❌ Промокод уже активирован"
    
    bonus = promos[promo_code]["bonus"]
    user["requests"] += bonus
    user["used_promos"].append(promo_code)
    promos[promo_code]["used"] = True
    
    save_user_data(load_user_data())
    save_promocodes(promos)
    return True, f"✅ +{bonus} запросов"

# ============================================
# SHERLOCK
# ============================================

def sherlock_search(query):
    return {
        'login': f"demo_user_{random.randint(1000,9999)}",
        'email': f"demo_{random.randint(100,999)}@example.com",
        'password': f"Demo{random.randint(100,999)}",
        'city': random.choice(["Москва", "СПб", "Новосибирск", "Казань", "Екатеринбург"]),
        'phone': query
    }

# ============================================
# MAP SEARCH
# ============================================

def search_address(query):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': query, 'format': 'json', 'limit': 1, 'accept-language': 'ru'}
        headers = {'User-Agent': 'sherlock_bot/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            return {'address': data[0]['display_name'], 'lat': float(data[0]['lat']), 'lon': float(data[0]['lon'])}
        return None
    except:
        return None

def get_map_buttons(lat, lon):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🗺️ Яндекс", url=f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map"),
        InlineKeyboardButton("🗺️ 2ГИС", url=f"https://2gis.ru/geo/{lat},{lon}")
    )
    keyboard.add(
        InlineKeyboardButton("🗺️ Google Maps", url=f"https://www.google.com/maps?q={lat},{lon}")
    )
    return keyboard

# ============================================
# КОМАНДЫ
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🕵️ SHERLOCK", callback_data="sherlock"),
        InlineKeyboardButton("🗺️ MAP SEARCH", callback_data="mapsearch")
    )
    keyboard.add(
        InlineKeyboardButton("🎁 Промокод", callback_data="promo"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats")
    )
    keyboard.add(
        InlineKeyboardButton("📋 Список промокодов", callback_data="promo_list")
    )
    bot.reply_to(message, f"🕵️ SHERLOCK V2.0\n\n📊 Доступно запросов: {get_remaining_requests(user_id)}\n🔄 Обновляются в 00:00", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    remaining = get_remaining_requests(user_id)
    
    if call.data == "sherlock":
        if remaining <= 0:
            bot.send_message(user_id, "❌ Закончились запросы! Ждите 00:00 или используйте промокод.")
            return
        msg = bot.send_message(user_id, "🕵️ Введите номер или почту:")
        bot.register_next_step_handler(msg, process_sherlock)
    
    elif call.data == "mapsearch":
        if remaining <= 0:
            bot.send_message(user_id, "❌ Закончились запросы! Ждите 00:00 или используйте промокод.")
            return
        msg = bot.send_message(user_id, "🗺️ Введите адрес:")
        bot.register_next_step_handler(msg, process_mapsearch)
    
    elif call.data == "promo":
        msg = bot.send_message(user_id, "🎁 Введите промокод:")
        bot.register_next_step_handler(msg, process_promo)
    
    elif call.data == "promo_list":
        promos = load_promocodes()
        text = "🎁 ПРОМОКОДЫ:\n\n"
        for code, data in promos.items():
            text += f"{'❌' if data.get('used') else '✅'} `{code}` — +{data['bonus']} запросов\n"
        bot.send_message(user_id, text, parse_mode='Markdown')
    
    elif call.data == "stats":
        bot.send_message(user_id, f"📊 Доступно запросов: {remaining}\n📅 {datetime.now().strftime('%d.%m.%Y')}")

def process_promo(message):
    success, result = use_promocode(message.chat.id, message.text.strip())
    bot.reply_to(message, result)
    bot.reply_to(message, f"📊 Осталось: {get_remaining_requests(message.chat.id)}")

def process_sherlock(message):
    user_id = message.chat.id
    query = message.text.strip()
    if not query or not use_request(user_id):
        bot.reply_to(message, "❌ Ошибка")
        return
    data = sherlock_search(query)
    bot.reply_to(message, f"✅ РЕЗУЛЬТАТ\n\n📱 {data['phone']}\n👤 {data['login']}\n📧 {data['email']}\n🔑 {data['password']}\n📍 {data['city']}\n\n⚠️ Демо-данные!")
    bot.reply_to(message, f"📊 Осталось: {get_remaining_requests(user_id)}")

def process_mapsearch(message):
    user_id = message.chat.id
    query = message.text.strip()
    if not query or not use_request(user_id):
        bot.reply_to(message, "❌ Ошибка")
        return
    result = search_address(query)
    if result:
        bot.reply_to(message, f"✅ НАЙДЕНО\n📍 {result['address']}\n🗺️ {result['lat']}, {result['lon']}", reply_markup=get_map_buttons(result['lat'], result['lon']))
    else:
        bot.reply_to(message, "❌ Адрес не найден")
    bot.reply_to(message, f"📊 Осталось: {get_remaining_requests(user_id)}")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    print("🕵️ SHERLOCK V2.0 запущен!")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10)
