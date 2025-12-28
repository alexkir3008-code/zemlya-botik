# bot.py
# Бот для ресторана "Земля", Самара
# Версия: 1.0
# Запуск: python bot.py

import os
import logging
import qrcode
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3

# === НАСТРОЙКИ ===
TOKEN = "8543698143:AAGrKeLeXS09P3gP85BgCKlIAH12EkinmQ0"  # ← Замени на свой
ADMIN_ID = 5041079358  # ← Твой ID (узнай у @userinfobot)

# Проверка токена (пропущена — токен уже настоящий)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# === Инициализация базы данных ===
def init_db():
    with sqlite3.connect("restaurant.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                bonus_points INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                items TEXT,
                total REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    print("✅ База данных создана")

# === FSM ===
class Registration(StatesGroup):
    waiting_for_phone = State()

# === ✅ ПОЛНОЕ МЕНЮ С ВЕСОМ И ОБЪЁМОМ ===
MENU = {
    "Холодные закуски": [
        {"name": "Рулетики из баклажанов", "price": 520, "desc": "5 шт."},
        {"name": "Рулетики из ветчины с сыром", "price": 570, "desc": "5 шт."},
        {"name": "Рулетики из кабачка с курицей", "price": 560, "desc": "5 шт."},
        {"name": "Брускетта с форелью", "price": 289, "desc": "1 шт."},
        {"name": "Брускетта с ростбифом", "price": 330, "desc": "1 шт."},
        {"name": "Брускетта с креветкой", "price": 350, "desc": "1 шт."},
        {"name": "Тарталетки с красной икрой", "price": 1450, "desc": "5 шт."},
        {"name": "Рулетики из форели с пармезаном", "price": 810, "desc": "5 шт."},
        {"name": "Рулетики из печеного перца", "price": 560, "desc": "5 шт."},
        {"name": "Ассорти тарталеток", "price": 1300, "desc": "С ростбифом 3 шт, с форелью 3 шт, с креветкой 3 шт — всего 9 шт."},
        {"name": "Капрезе", "price": 500, "desc": "150 г"},
        {"name": "Утиная ножка с пьяной грушей", "price": 1130, "desc": "280 г"},
        {"name": "Медальоны из говяжьей вырезки", "price": 1570, "desc": "270 г"},
        {"name": "Медальоны из свиной вырезки", "price": 700, "desc": "200 г"},
        {"name": "Ассорти морепродуктов", "price": 7000, "desc": "830 г"},
        {"name": "Запеченная буженина", "price": 3700, "desc": "1,7 кг (с молодым картофелем, свежими овощами)"},
        {"name": "Судак фаршированный", "price": 7300, "desc": "2 кг"},
        {"name": "Ассорти шашлыков", "price": 6780, "desc": "2 400 г (курица, свинина, баранина, говядина, овощи)"},
        {"name": "Томленая баранья нога", "price": 10000, "desc": "3 кг"},
    ],
    "Горячие блюда": [
        {"name": "Пельмени с говядиной", "price": 330, "desc": "270 г"},
        {"name": "Манты с говядиной", "price": 125, "desc": "1 шт."},
        {"name": "Рулька с квашеной капустой", "price": 1250, "desc": "600 г"},
        {"name": "Бефстроганов", "price": 620, "desc": "С картофельным пюре"},
        {"name": "Стейк из куриной грудки", "price": 590},
        {"name": "Стейк из судака", "price": 700, "desc": "С креветочным соусом"},
        {"name": "Шашлык из цыпленка", "price": 650, "desc": "180 г шашлыка + 100 г картофеля — 280 г"},
        {"name": "Шашлык из свиной шеи", "price": 690, "desc": "180 г шашлыка + 100 г картофеля — 280 г"},
        {"name": "Запеченные баклажаны", "price": 590, "desc": "300 г (с мясным соусом, острый)"},
        {"name": "Бургер с говядиной", "price": 550},
    ],
    "Фирменные настойки": [
        {"name": "Напиток классический", "price": 150, "desc": "50 мл"},
        {"name": "Беленькая", "price": 150, "desc": "50 мл"},
        {"name": "Хреновуха", "price": 150, "desc": "50 мл"},
        {"name": "Зубровка", "price": 150, "desc": "50 мл"},
        {"name": "Имбирно-ореховая", "price": 150, "desc": "50 мл"},
        {"name": "Клубника чили", "price": 150, "desc": "50 мл"},
        {"name": "Малинка", "price": 150, "desc": "50 мл"},
        {"name": "Вишенка", "price": 150, "desc": "50 мл"},
        {"name": "Клюковка", "price": 150, "desc": "50 мл"},
        {"name": "Смородинка", "price": 150, "desc": "50 мл"},
    ],
    "Безалкогольные напитки": [
        {"name": "Вода Bon Aqua", "price": 100, "desc": "330 мл (с газом/без)"},
        {"name": "Вода Borjomi", "price": 285, "desc": "500 мл"},
        {"name": "Морс", "price": 140, "desc": "200 мл"},
        {"name": "Морс большой", "price": 500, "desc": "700 мл"},
        {"name": "Сок Rich", "price": 200, "desc": "200 мл (апельсин, яблоко, вишня)"},
        {"name": "Coca Cola", "price": 170, "desc": "300 мл"},
        {"name": "Sprite", "price": 170, "desc": "300 мл"},
        {"name": "Fanta", "price": 170, "desc": "300 мл"},
    ],
    "Вино": [
        {"name": "Chianti (красное)", "price": 320, "desc": "125 мл"},
        {"name": "Chianti бутылка", "price": 2100, "desc": "750 мл"},
        {"name": "Pinot Grigio", "price": 320, "desc": "125 мл (белое сухое)"},
        {"name": "Pinot Grigio бутылка", "price": 1900, "desc": "750 мл"},
        {"name": "Riesling", "price": 400, "desc": "125 мл (белое сухое)"},
        {"name": "Riesling бутылка", "price": 2400, "desc": "750 мл"},
        {"name": "Prosecco", "price": 2400, "desc": "750 мл"},
    ],
    "Салаты": [
        {"name": "Оливье с цыплёнком", "price": 360},
        {"name": "Оливье с баклажанами", "price": 460, "desc": "С хрустящими баклажанами и творожным сыром"},
        {"name": "Цезарь с цыплёнком", "price": 480},
        {"name": "Цезарь с креветками", "price": 580},
        {"name": "Греческий салат", "price": 440, "desc": "С оливковым маслом"},
        {"name": "Салат из квашеной капусты", "price": 150, "desc": "150 г"},
        {"name": "Салат ростбиф", "price": 500, "desc": "260 г (говядина, руккола, овощи, грибы, горчичный соус)"},
    ],
    "Кофе": [
        {"name": "Эспрессо", "price": 120, "desc": "30 мл"},
        {"name": "Американо", "price": 170, "desc": "150 мл"},
        {"name": "Капучино обычное", "price": 220, "desc": "200 мл"},
        {"name": "Капучино альтернативное", "price": 250, "desc": "200 мл (миндальное/кокосовое молоко)"},
        {"name": "Латте обычное", "price": 250, "desc": "220 мл"},
        {"name": "Латте альтернативное", "price": 280, "desc": "220 мл"},
    ],
    "Лимонады": [
        {"name": "Лимонад Маракуйя-Кинза", "price": 200, "desc": "200 мл"},
        {"name": "Лимонад Маракуйя-Кинза большой", "price": 750, "desc": "750 мл"},
        {"name": "Лимонад Киви-Сельдерей", "price": 200, "desc": "200 мл"},
        {"name": "Лимонад Киви-Сельдерей большой", "price": 750, "desc": "750 мл"},
        {"name": "Лимонад Брусника-Щавель", "price": 200, "desc": "200 мл"},
        {"name": "Лимонад Брусника-Щавель большой", "price": 750, "desc": "750 мл"},
    ],
    "Чай": [
        {"name": "Ассам", "price": 250, "desc": "700 мл (черный)"},
        {"name": "Сенча", "price": 250, "desc": "700 мл (зеленый)"},
        {"name": "Эрл Грей", "price": 250, "desc": "700 мл"},
        {"name": "Жасмин", "price": 250, "desc": "700 мл"},
        {"name": "Молочный улун", "price": 250, "desc": "700 мл"},
        {"name": "Чай Фруктовый", "price": 400, "desc": "700 мл (авторский)"},
        {"name": "Чай Ягодный", "price": 400, "desc": "700 мл"},
        {"name": "Чай Цитрусовый", "price": 400, "desc": "700 мл"},
    ],
    "Гарниры": [
        {"name": "Картофель запечённый", "price": 280, "desc": "С розмарином"},
        {"name": "Картофель фри", "price": 280},
        {"name": "Картофель пюре", "price": 280},
        {"name": "Рис с овощами", "price": 280},
    ],
    "Хлеб": [
        {"name": "Хлеб пшеничный", "price": 15, "desc": "25 г"},
        {"name": "Хлеб ржаной", "price": 15, "desc": "25 г"},
    ],
    "Десерты": [
        {"name": "Чизкейк классический", "price": 350, "desc": "120 г"},
        {"name": "Штрудель яблочный/вишневый", "price": 350, "desc": "160 г"},
        {"name": "Мороженое", "price": 95, "desc": "1 шт. (ваниль, шоколад, клубника)"},
        {"name": "Кекс морковный", "price": 180, "desc": "100 г"},
    ],
    "Супы": [
        {"name": "Борщ с говядиной", "price": 460},
        {"name": "Грибной крем-суп", "price": 350},
        {"name": "Том ям", "price": 590},
        {"name": "Куриный с лапшой", "price": 360},
        {"name": "Уха с форелью и судаком", "price": 590},
    ],
    "Завтраки": [
        {"name": "Блинчики со шпинатом и форелью", "price": 350, "desc": "2 шт."},
        {"name": "Каша киноа", "price": 170, "desc": "150 г (+форель, авокадо, яйцо, пармезан)"},
        {"name": "Омлет с форелью", "price": 350, "desc": "300 г (свежие овощи)"},
        {"name": "Сырники творожные", "price": 250},
        {"name": "Яичница из 3 яиц", "price": 190, "desc": "Дополнительно: +бекон, +колбаски, +форель, +овощи"},
        {"name": "Блинчики", "price": 150, "desc": "2 шт. Дополнительно: +варенье, +мёд, +сметана"},
        {"name": "Каша гречневая", "price": 120, "desc": "150 г (+форель, авокадо, яйцо, пармезан)"},
        {"name": "Каша овсяная", "price": 120},
    ],
}

# === /start ===
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    with sqlite3.connect("restaurant.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone, bonus_points FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

    if user:
        await message.answer(
            f"Добро пожаловать, {first_name}! 🌿\n"
            f"Ваш номер: {user[0]}\n"
            f"Бонусы: {user[1]} ₽\n"
            f"Ждём вас в «Земле»!\n/start_menu — меню"
        )
    else:
        kb = [[types.KeyboardButton(text="📱 Отправить номер", request_contact=True)]]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer(
            f"Привет, {first_name}! 👋\n"
            "Добро пожаловать в ресторан «Земля».\n"
            "Поделитесь номером для бонусной программы:",
            reply_markup=keyboard
        )
        await state.set_state(Registration.waiting_for_phone)

@dp.message(Registration.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""

    with sqlite3.connect("restaurant.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, first_name, last_name, phone, bonus_points)
            VALUES (?, ?, ?, ?, COALESCE((SELECT bonus_points FROM users WHERE user_id = ?), 0))
        """, (user_id, first_name, last_name, phone, user_id))
        conn.commit()

    await message.answer(
        f"Спасибо, {first_name}! 🎉\n"
        "Вы зарегистрированы. Пользуйтесь ботом!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()

# === Главное меню ===
@dp.message(Command("start_menu"))
async def main_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🍽 Меню", callback_data="menu")],
        [types.InlineKeyboardButton(text="💰 Мои бонусы", callback_data="bonus_balance")],
        [types.InlineKeyboardButton(text="🍽 История заказов", callback_data="order_history")],
        [types.InlineKeyboardButton(text="🎁 Персональные акции", callback_data="offers")],
        [types.InlineKeyboardButton(text="🔔 Подписаться", callback_data="subscribe")]
    ])
    await message.answer("โปรแ  Добро пожаловать в «Земля»!", reply_markup=kb)

# === Меню ===
@dp.callback_query(F.data == "menu")
async def show_menu_categories(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    for cat in MENU.keys():
        keyboard.inline_keyboard.append([types.InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}")])
    keyboard.inline_keyboard.append([types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    await call.message.edit_text("🍽 Выберите категорию:", reply_markup=keyboard)
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_dishes(call: types.CallbackQuery):
    category = call.data[4:]
    dishes = MENU.get(category, [])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    for i, dish in enumerate(dishes):
        desc = f" ({dish['desc']})" if 'desc' in dish else ""
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"{dish['name']} — {dish['price']} ₽{desc}",
                callback_data=f"dish_{category}_{i}"
            )
        ])
    keyboard.inline_keyboard.append([
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="start_menu"),
        types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    ])
    await call.message.edit_text(f"🍽 <b>{category}</b>", reply_markup=keyboard, parse_mode="HTML")
    await call.answer()

# === QR-код ===
@dp.callback_query(F.data == "bonus_balance")
async def bonus_balance(call: types.CallbackQuery):
    user_id = call.from_user.id
    with sqlite3.connect("restaurant.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT bonus_points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

    if not result:
        await call.message.answer("❌ Пользователь не найден.")
        await call.answer()
        return

    points = result[0]
    qr_data = f"ZEMLYA:BONUS:{user_id}:{int(call.message.date.timestamp())}"
    qr_img = qrcode.make(qr_data)

    bio = BytesIO()
    qr_img.save(bio, "PNG")
    bio.seek(0)

    await call.message.answer_photo(
        photo=types.BufferedInputFile(bio.getvalue(), filename="qrcode.png"),
        caption=f"🧾 Ваши бонусы: {points} ₽\n\n"
                "Покажите QR-код официанту для начисления."
    )
    await call.answer()

# === Запуск ===
async def main():
    init_db()
    print("🚀 Бот запущен. Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())