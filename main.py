import telebot
from telebot import types
import datetime
import re

bot = telebot.TeleBot("7858465354:AAEmhBMVosGXMFo0ah64GgPe8me0_umkwwA")  # Tokenni kiriting
orders_file = "orders.txt"

# Elektronika mahsulotlari va kategoriyalar
categories = {
    "📱 Mobil telefonlar": {
        "Samsung Galaxy S21": 1200000,
        "iPhone 13": 1500000,
        "Xiaomi Mi 11": 900000
    },
    "💻 Kompyuterlar": {
        "Lenovo ThinkPad": 2000000,
        "MacBook Pro": 2500000,
        "HP Pavilion": 1800000
    },
    "🎧 Aksessuarlar": {
        "AirPods Pro": 350000,
        "Beats Headphones": 450000,
        "Samsung Earbuds": 300000
    }
}

savatcha = {}
user_states = {}

# === FOYDALI FUNKSIYALAR ===
def is_valid_phone(phone):
    return bool(re.match(r'^\+998(93|94|50|51|88|95|97|98|99|33)\d{7}$', phone))

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📜 Kategoriyalar", "🛒 Savatcha")
    markup.row("📦 Buyurtma berish", "🎁 Aksiya")
    markup.row("📍 Manzil")
    return markup

def categories_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in categories:
        markup.add(category)
    markup.add("🔙 Ortga")
    return markup

def products_buttons(category):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for product, price in categories[category].items():
        markup.add(f"➕ {product} - {price} so'm")
    markup.add("🔙 Ortga")
    return markup

def tolov_buttons():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Payme", url="https://payme.uz"))
    markup.add(types.InlineKeyboardButton("💳 Click", url="https://click.uz"))
    return markup

# === START ===
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Assalomu alaykum! Elektronika do‘konimizga xush kelibsiz.", reply_markup=main_menu())

# === KATEGORIYALAR ===
@bot.message_handler(func=lambda msg: msg.text == "📜 Kategoriyalar")
def show_categories(message):
    bot.send_message(message.chat.id, "📚 Mahsulot kategoriyalarini tanlang:", reply_markup=categories_buttons())

@bot.message_handler(func=lambda msg: msg.text == "🔙 Ortga")
def go_back(message):
    bot.send_message(message.chat.id, "🔙 Asosiy menyuga qaytdingiz.", reply_markup=main_menu())

# === MAHSULOTLAR ===
@bot.message_handler(func=lambda message: message.text in categories)
def show_products(message):
    category = message.text
    bot.send_message(message.chat.id, f"📦 {category} mahsulotlari:", reply_markup=products_buttons(category))

@bot.message_handler(func=lambda message: message.text.startswith("➕"))
def add_to_cart(message):
    try:
        product_info = message.text.replace("➕ ", "").split(" - ")
        product_name = product_info[0]
        product_price = int(product_info[1].replace(" so'm", ""))
        savatcha.setdefault(message.from_user.id, []).append((product_name, product_price))
        bot.send_message(message.chat.id, f"✅ {product_name} savatchaga qo‘shildi.")
    except:
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko‘ring.")

# === SAVATCHA ===
@bot.message_handler(func=lambda msg: msg.text == "🛒 Savatcha")
def view_cart(message):
    items = savatcha.get(message.from_user.id, [])
    if not items:
        bot.send_message(message.chat.id, "Savatchangiz bo‘sh.")
        return
    text = "🛒 Savatchangiz:\n"
    total = 0
    for item, price in items:
        text += f"- {item} ({price} so'm)\n"
        total += price
    text += f"\nJami: {total} so‘m"
    bot.send_message(message.chat.id, text, reply_markup=tolov_buttons())

# === BUYURTMA BERISH ===
@bot.message_handler(func=lambda msg: msg.text == "📦 Buyurtma berish")
def order_start(message):
    user_states[message.chat.id] = {"step": "name"}
    bot.send_message(message.chat.id, "Ismingizni kiriting:")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "name")
def get_name(message):
    user_states[message.chat.id]["name"] = message.text
    user_states[message.chat.id]["step"] = "phone"
    bot.send_message(message.chat.id, "Telefon raqamingizni kiriting (masalan, +99893xxxxxxx):")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "phone")
def get_phone(message):
    if not is_valid_phone(message.text):
        bot.send_message(message.chat.id, "⚠ Raqam noto‘g‘ri. +998 bilan kiriting.")
        return
    user_states[message.chat.id]["phone"] = message.text
    user_states[message.chat.id]["step"] = "address"
    bot.send_message(message.chat.id, "Manzilingizni kiriting:")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "address")
def get_address(message):
    user_states[message.chat.id]["address"] = message.text
    user_states[message.chat.id]["step"] = "confirm"
    bot.send_message(message.chat.id, "Buyurtmani tasdiqlaysizmi? (Ha/Yoq)")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "confirm")
def confirm_order(message):
    if message.text.lower() != "ha":
        bot.send_message(message.chat.id, "❌ Buyurtma bekor qilindi.", reply_markup=main_menu())
        user_states.pop(message.chat.id, None)
        return

    data = user_states[message.chat.id]
    items = savatcha.get(message.from_user.id, [])
    if not items:
        bot.send_message(message.chat.id, "❌ Savatchangiz bo‘sh. Avval mahsulot tanlang.", reply_markup=main_menu())
        return

    total = sum([price for _, price in items])
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    order_text = f"Buyurtma ({time}):\nIsm: {data['name']}\nTel: {data['phone']}\nManzil: {data['address']}\n\n"
    order_text += "\n".join([f"{item} - {price} so'm" for item, price in items])
    order_text += f"\nJami: {total} so‘m\n"

    with open(orders_file, "a", encoding="utf-8") as f:
        f.write(order_text + "\n---\n")

    savatcha.pop(message.from_user.id, None)
    user_states.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "✅ Buyurtma qabul qilindi. Tez orada siz bilan bog‘lanamiz.", reply_markup=main_menu())

# === AKSIYA VA MANZIL ===
@bot.message_handler(func=lambda msg: msg.text == "📍 Manzil")
def manzil(message):
    bot.send_message(message.chat.id, "📍 Navoiy shahar, Mustaqillik ko‘chasi 12-uy")

@bot.message_handler(func=lambda msg: msg.text == "🎁 Aksiya")
def aksiya(message):
    bot.send_message(message.chat.id, "🎉 Bugungi aksiya: Mobil telefonlar va aksessuarlar 10% chegirma bilan!")

# === ISHGA TUSHURISH ===
bot.polling()
