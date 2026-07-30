#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random
import requests
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ДАННЫХ
# ============================================

DATA_FILE = "user_data.json"
PROMO_FILE = "promocodes.json"

# ============================================
# ЗАГРУЗКА ПРОМОКОДОВ ИЗ ФАЙЛА
# ============================================

def load_promocodes():
    """Загружает промокоды из файла"""
    if os.path.exists(PROMO_FILE):
        try:
            with open(PROMO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки промокодов: {e}")
    
    # Если файла нет — создаём с базовыми
    default_promos = {
        "220811": {"bonus": 3, "description": "Базовый промокод", "used": False},
        "22081110": {"bonus": 10, "description": "Расширенный промокод", "used": False},
        "gsa22": {"bonus": 3, "description": "Специальный промокод", "used": False}
    }
    save_promocodes(default_promos)
    return default_promos

def save_promocodes(promos):
    """Сохраняет промокоды в файл"""
    try:
        with open(PROMO_FILE, "w", encoding="utf-8") as f:
            json.dump(promos, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения промокодов: {e}")
        return False

def reload_promocodes():
    """Перезагружает промокоды из файла (для админа)"""
    return load_promocodes()

# ============================================
# РАБОТА С ДАННЫМИ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    data = load_user_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "requests": 1,
            "last_date": datetime.now().strftime("%Y-%m-%d"),
            "used_promos": []
        }
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

# ============================================
# РАБОТА С ПРОМОКОДАМИ
# ============================================

def use_promocode(user_id, promo_code):
    """Активирует промокод для пользователя"""
    user = get_user(user_id)
    promos = load_promocodes()
    
    if promo_code not in promos:
        return False, "❌ Неверный промокод"
    
    if promo_code in user["used_promos"]:
        return False, "❌ Вы уже использовали этот промокод"
    
    if promos[promo_code].get("used", False):
        return False, "❌ Промокод уже активирован другим пользователем"
    
    # Активируем
    bonus = promos[promo_code]["bonus"]
    user["requests"] += bonus
    user["used_promos"].append(promo_code)
    promos[promo_code]["used"] = True
    
    save_user_data(load_user_data())
    save_promocodes(promos)
    
    return True, f"✅ Промокод активирован! +{bonus} запросов"

def get_all_promocodes():
    """Возвращает список всех промокодов с описанием"""
    promos = load_promocodes()
    result = "🎁 ДОСТУПНЫЕ ПРОМОКОДЫ:\n\n"
    for code, data in promos.items():
        status = "❌" if data.get("used", False) else "✅"
        result += f"{status} `{code}` — +{data['bonus']} запросов\n"
        if data.get("description"):
            result += f"   📝 {data['description']}\n"
    return result

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
    user_id = message.chat.id
    remaining = get_remaining_requests(user_id)
    
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
    
    bot.reply_to(
        message,
        f"🕵️ SHERLOCK V2.0\n\n"
        f"📊 Доступно запросов: {remaining}\n"
        f"🔄 Обновляются в 00:00\n\n"
        f"Выберите режим:",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['promo'])
def promo_command(message):
    msg = bot.reply_to(message, "🎁 Введите промокод:")
    bot.register_next_step_handler(msg, process_promo)

@bot.message_handler(commands=['promolist'])
def promolist_command(message):
    bot.reply_to(message, get_all_promocodes(), parse_mode='Markdown')

@bot.message_handler(commands=['reload_promo'])
def reload_promo_command(message):
    """Админская команда для перезагрузки промокодов"""
    # Простая проверка — только для вас
    if message.chat.id == 8897234847:  # замените на ваш ID
        promos = reload_promocodes()
        bot.reply_to(message, f"✅ Промокоды перезагружены! Загружено {len(promos)} промокодов.")
    else:
        bot.reply_to(message, "❌ У вас нет прав для этой команды")

def process_promo(message):
    user_id = message.chat.id
    promo = message.text.strip()
    
    success, result = use_promocode(user_id, promo)
    bot.reply_to(message, result)
    
    remaining = get_remaining_requests(user_id)
    bot.reply_to(message, f"📊 Осталось запросов: {remaining}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    remaining = get_remaining_requests(user_id)
    
    if call.data == "sherlock":
        if remaining <= 0:
            bot.send_message(user_id, "❌ Закончились запросы на сегодня!\n🔄 Ждите 00:00 или используйте промокод.")
            return
        
        msg = bot.send_message(user_id, "🕵️ Введите номер телефона или почту для поиска:")
        bot.register_next_step_handler(msg, process_sherlock)
    
    elif call.data == "mapsearch":
        if remaining <= 0:
            bot.send_message(user_id, "❌ Закончились запросы на сегодня!\n🔄 Ждите 00:00 или используйте промокод.")
            return
        
        msg = bot.send_message(user_id, "🗺️ Введите адрес для поиска на карте:")
        bot.register_next_step_handler(msg, process_mapsearch)
    
    elif call.data == "promo":
        msg = bot.send_message(user_id, "🎁 Введите промокод:")
        bot.register_next_step_handler(msg, process_promo)
    
    elif call.data == "promo_list":
        bot.send_message(user_id, get_all_promocodes(), parse_mode='Markdown')
    
    elif call.data == "stats":
        total = get_remaining_requests(user_id)
        bot.send_message(
            user_id,
            f"📊 ВАША СТАТИСТИКА:\n\n"
            f"📌 Доступно запросов: {total}\n"
            f"🔄 Обновление в 00:00\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}"
        )

def process_sherlock(message):
    user_id = message.chat.id
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    if not use_request(user_id):
        bot.reply_to(message, "❌ Закончились запросы!")
        return
    
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
    
    remaining = get_remaining_requests(user_id)
    bot.reply_to(message, f"📊 Осталось запросов: {remaining}")

def process_mapsearch(message):
    user_id = message.chat.id
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    if not use_request(user_id):
        bot.reply_to(message, "❌ Закончились запросы!")
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
    
    remaining = get_remaining_requests(user_id)
    bot.reply_to(message, f"📊 Осталось запросов: {remaining}")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    # Создаём файл с промокодами, если его нет
    load_promocodes()
    
    while True:
        try:
            print("🕵️ SHERLOCK V2.0 запущен!")
            print(f"📁 Файл промокодов: {PROMO_FILE}")
            promos = load_promocodes()
            print(f"🎁 Загружено промокодов: {len(promos)}")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10) #!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import time
import random
import requests
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8897234847:AAGxGxpixo2746NwJP_Hw7n4wXQ-tRzWD2I"
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ДАННЫХ
# ============================================

DATA_FILE = "user_data.json"
PROMO_FILE = "promocodes.json"

# ============================================
# ЗАГРУЗКА ПРОМОКОДОВ ИЗ ФАЙЛА
# ============================================

def load_promocodes():
    """Загружает промокоды из файла"""
    if os.path.exists(PROMO_FILE):
        try:
            with open(PROMO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки промокодов: {e}")
    
    # Если файла нет — создаём с базовыми
    default_promos = {
        "220811": {"bonus": 3, "description": "Базовый промокод", "used": False},
        "22081110": {"bonus": 10, "description": "Расширенный промокод", "used": False},
        "gsa22": {"bonus": 3, "description": "Специальный промокод", "used": False}
    }
    save_promocodes(default_promos)
    return default_promos

def save_promocodes(promos):
    """Сохраняет промокоды в файл"""
    try:
        with open(PROMO_FILE, "w", encoding="utf-8") as f:
            json.dump(promos, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения промокодов: {e}")
        return False

def reload_promocodes():
    """Перезагружает промокоды из файла (для админа)"""
    return load_promocodes()

# ============================================
# РАБОТА С ДАННЫМИ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    data = load_user_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "requests": 1,
            "last_date": datetime.now().strftime("%Y-%m-%d"),
            "used_promos": []
        }
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

# ============================================
# РАБОТА С ПРОМОКОДАМИ
# ============================================

def use_promocode(user_id, promo_code):
    """Активирует промокод для пользователя"""
    user = get_user(user_id)
    promos = load_promocodes()
    
    if promo_code not in promos:
        return False, "❌ Неверный промокод"
    
    if promo_code in user["used_promos"]:
        return False, "❌ Вы уже использовали этот промокод"
    
    if promos[promo_code].get("used", False):
        return False, "❌ Промокод уже активирован другим пользователем"
    
    # Активируем
    bonus = promos[promo_code]["bonus"]
    user["requests"] += bonus
    user["used_promos"].append(promo_code)
    promos[promo_code]["used"] = True
    
    save_user_data(load_user_data())
    save_promocodes(promos)
    
    return True, f"✅ Промокод активирован! +{bonus} запросов"

def get_all_promocodes():
    """Возвращает список всех промокодов с описанием"""
    promos = load_promocodes()
    result = "🎁 ДОСТУПНЫЕ ПРОМОКОДЫ:\n\n"
    for code, data in promos.items():
        status = "❌" if data.get("used", False) else "✅"
        result += f"{status} `{code}` — +{data['bonus']} запросов\n"
        if data.get("description"):
            result += f"   📝 {data['description']}\n"
    return result

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
    user_id = message.chat.id
    remaining = get_remaining_requests(user_id)
    
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
    
    bot.reply_to(
        message,
        f"🕵️ SHERLOCK V2.0\n\n"
        f"📊 Доступно запросов: {remaining}\n"
        f"🔄 Обновляются в 00:00\n\n"
        f"Выберите режим:",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['promo'])
def promo_command(message):
    msg = bot.reply_to(message, "🎁 Введите промокод:")
    bot.register_next_step_handler(msg, process_promo)

@bot.message_handler(commands=['promolist'])
def promolist_command(message):
    bot.reply_to(message, get_all_promocodes(), parse_mode='Markdown')

@bot.message_handler(commands=['reload_promo'])
def reload_promo_command(message):
    """Админская команда для перезагрузки промокодов"""
    # Простая проверка — только для вас
    if message.chat.id == 8897234847:  # замените на ваш ID
        promos = reload_promocodes()
        bot.reply_to(message, f"✅ Промокоды перезагружены! Загружено {len(promos)} промокодов.")
    else:
        bot.reply_to(message, "❌ У вас нет прав для этой команды")

def process_promo(message):
    user_id = message.chat.id
    promo = message.text.strip()
    
    success, result = use_promocode(user_id, promo)
    bot.reply_to(message, result)
    
    remaining = get_remaining_requests(user_id)
    bot.reply_to(message, f"📊 Осталось запросов: {remaining}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    remaining = get_remaining_requests(user_id)
    
    if call.data == "sherlock":
        if remaining <= 0:
            bot.send_message(user_id, "❌ Закончились запросы на сегодня!\n🔄 Ждите 00:00 или используйте промокод.")
            return
        
        msg = bot.send_message(user_id, "🕵️ Введите номер телефона или почту для поиска:")
        bot.register_next_step_handler(msg, process_sherlock)
    
    elif call.data == "mapsearch":
        if remaining <= 0:
            bot.send_message(user_id, "❌ Закончились запросы на сегодня!\n🔄 Ждите 00:00 или используйте промокод.")
            return
        
        msg = bot.send_message(user_id, "🗺️ Введите адрес для поиска на карте:")
        bot.register_next_step_handler(msg, process_mapsearch)
    
    elif call.data == "promo":
        msg = bot.send_message(user_id, "🎁 Введите промокод:")
        bot.register_next_step_handler(msg, process_promo)
    
    elif call.data == "promo_list":
        bot.send_message(user_id, get_all_promocodes(), parse_mode='Markdown')
    
    elif call.data == "stats":
        total = get_remaining_requests(user_id)
        bot.send_message(
            user_id,
            f"📊 ВАША СТАТИСТИКА:\n\n"
            f"📌 Доступно запросов: {total}\n"
            f"🔄 Обновление в 00:00\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}"
        )

def process_sherlock(message):
    user_id = message.chat.id
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    if not use_request(user_id):
        bot.reply_to(message, "❌ Закончились запросы!")
        return
    
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
    
    remaining = get_remaining_requests(user_id)
    bot.reply_to(message, f"📊 Осталось запросов: {remaining}")

def process_mapsearch(message):
    user_id = message.chat.id
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пустой запрос")
        return
    
    if not use_request(user_id):
        bot.reply_to(message, "❌ Закончились запросы!")
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
    
    remaining = get_remaining_requests(user_id)
    bot.reply_to(message, f"📊 Осталось запросов: {remaining}")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    # Создаём файл с промокодами, если его нет
    load_promocodes()
    
    while True:
        try:
            print("🕵️ SHERLOCK V2.0 запущен!")
            print(f"📁 Файл промокодов: {PROMO_FILE}")
            promos = load_promocodes()
            print(f"🎁 Загружено промокодов: {len(promos)}")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(10)
