import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# 🔐 ВСТАВЬТЕ ВАШ РЕАЛЬНЫЙ ТОКЕН ЗДЕСЬ
BOT_TOKEN = "8251869795:AAHlTRYf2yXj7_OIFhTpOhr2ydijI7zGf_k"  # ← ЗАМЕНИТЕ НА ВАШ ТОКЕН

# Проверка токена
if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
    print("❌ ОШИБКА: Замените BOT_TOKEN на ваш реальный токен!")
    print("📝 Как получить токен:")
    print("1. Напишите @BotFather в Telegram")
    print("2. Отправьте /newbot")
    print("3. Следуйте инструкциям")
    print("4. Скопируйте токен и вставьте в код")
    exit(1)

# Инициализация бота
try:
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("✅ Бот успешно инициализирован!")
except Exception as e:
    print(f"❌ Ошибка инициализации бота: {e}")
    exit(1)

# 🔧 ВСТАВЬТЕ ВАШ ТЕЛЕГРАМ ID
ADMIN_IDS = [1148740361]  # ← ВАШ ID ЗДЕСЬ

# Доступные статусы заказов
ORDER_STATUSES = {
    "new": "🆕 Новый",
    "processing": "🔄 В обработке",
    "confirmed": "✅ Подтвержден",
    "packing": "📦 Сборка",
    "shipped": "🚚 Отправлен",
    "delivered": "📬 Доставлен",
    "cancelled": "❌ Отменен"
}


def is_admin(user_id):
    return user_id in ADMIN_IDS


# Файл для сохранения данных
DATA_FILE = "bot_data.json"


# Загрузка данных из файла
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
    return {"carts": {}, "orders": {}, "order_counter": 1}


# Сохранение данных в файл
def save_data():
    try:
        data = {
            "carts": user_carts,
            "orders": user_orders,
            "order_counter": order_counter
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")


# Загружаем данные
data = load_data()
user_carts = data.get("carts", {})
user_orders = data.get("orders", {})
order_counter = data.get("order_counter", 1)

# Товары с фотографиями
products = {
    "зипка белая ": [
        {
            "id": 1,
            "name": "зипка с балаклавой ",
            "price": 1700,
            "sizes": ["S", "M", "L", "XL"],
            "description": "🔥 Классическая зипка из 100% хлопка премиум качества",
            "photo": "https://via.placeholder.com/400x400/0088cc/ffffff?text=T-Shirt",
            "details": "Материал: 100% хлопок\nВес: "
        },
    ],
    "зипка черная ": [
        {
            "id": 2,
            "name": "зипка с балаклавой =",
            "price": 1600,
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "description": "⚡ Футуристичное зипки с уникальным дизайном",
            "photo": "https://via.placeholder.com/400x400/00cc88/ffffff?text=Hoodie",
            "details": "Материал: 80% хлопок, 20% полиэстер\nВес:"
        },
    ],
}


# States для оформления заказа
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_shipping = State()
    waiting_for_payment = State()
    confirmation = State()


# States для админ-панели
class AdminState(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_sizes = State()
    waiting_for_product_photo = State()
    waiting_for_order_status = State()


# ==================== КЛАВИАТУРЫ ====================

def get_main_menu(user_id=None):
    builder = ReplyKeyboardBuilder()

    # Получаем количество товаров в корзине
    cart_count = 0
    if user_id and user_id in user_carts:
        cart_count = len(user_carts[user_id])

    builder.row(types.KeyboardButton(text="Каталог товаров"))
    builder.row(types.KeyboardButton(text=f"Карзина ({cart_count})"))
    builder.row(types.KeyboardButton(text="Мои заказы"))
    builder.row(types.KeyboardButton(text="Контакты"), types.KeyboardButton(text="Акции"))

    # Добавляем кнопку админ-панели для администраторов
    if is_admin(user_id):
        builder.row(types.KeyboardButton(text="👨‍💻 Админ-панель"))

    return builder.as_markup(resize_keyboard=True)


def get_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📦 Управление товарами"))
    builder.row(types.KeyboardButton(text="📊 Статистика"))
    builder.row(types.KeyboardButton(text="📋 Все заказы"))
    builder.row(types.KeyboardButton(text="👤 Обычное меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_products_management_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="🗑️ Удалить товар", callback_data="admin_delete_product")
    builder.button(text="📋 Список товаров", callback_data="admin_list_products")
    builder.button(text="📊 Статистика товаров", callback_data="admin_products_stats")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_order_management_kb(order_id=None):
    """Клавиатура для управления заказами"""
    builder = InlineKeyboardBuilder()

    if order_id:
        # Кнопки для конкретного заказа
        for status_key, status_name in ORDER_STATUSES.items():
            builder.button(text=f"📝 {status_name}", callback_data=f"set_status_{order_id}_{status_key}")
        builder.button(text="⬅️ Назад к заказам", callback_data="admin_all_orders")
    else:
        # Общие кнопки управления заказами
        builder.button(text="📋 Все заказы", callback_data="admin_all_orders")
        builder.button(text="🆕 Новые заказы", callback_data="admin_new_orders")
        builder.button(text="🚚 В доставке", callback_data="admin_shipping_orders")

    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_categories_kb():
    builder = InlineKeyboardBuilder()
    for category in products.keys():
        builder.button(text=category, callback_data=f"category_{category}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_categories_kb_admin():
    builder = InlineKeyboardBuilder()
    categories = list(products.keys())
    for category in categories:
        builder.button(text=category, callback_data=f"admin_category_{category}")
    builder.button(text="➕ Новая категория", callback_data="admin_new_category")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_products_kb(category, product_index=0):
    category_products = products[category]
    product = category_products[product_index]

    builder = InlineKeyboardBuilder()

    # Кнопки размеров
    for size in product["sizes"]:
        builder.button(text=size, callback_data=f"size_{product['id']}_{size}")

    # Навигация
    if product_index > 0:
        builder.button(text="⬅️ Назад", callback_data=f"product_{category}_{product_index - 1}")

    builder.button(text="🛒 Корзина", callback_data="view_cart")

    if product_index < len(category_products) - 1:
        builder.button(text="Далее ➡️", callback_data=f"product_{category}_{product_index + 1}")

    builder.button(text="📂 Каталог", callback_data="back_to_categories")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_cart_kb(user_id):
    cart = user_carts.get(user_id, [])
    builder = InlineKeyboardBuilder()

    for i, item in enumerate(cart):
        builder.button(
            text=f"❌ {item['name']} ({item['size']})",
            callback_data=f"remove_{i}"
        )

    if cart:
        builder.button(text="🧹 Очистить корзину", callback_data="clear_cart")
        builder.button(text="🚀 Оформить заказ", callback_data="checkout")

    builder.button(text="🛍️ В каталог", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


def get_shipping_methods_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📮 Почта России", callback_data="shipping_post")
    builder.button(text="🚚 СДЭК", callback_data="shipping_cdek")
    builder.adjust(2)
    return builder.as_markup()


def get_payment_methods_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Карта", callback_data="payment_card")
    builder.button(text="🤝 СБП", callback_data="payment_sbp")
    builder.button(text="💰 При получении", callback_data="payment_cod")
    builder.adjust(2)
    return builder.as_markup()


def get_confirmation_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    builder.button(text="✏️ Исправить данные", callback_data="edit_order")
    builder.adjust(1)
    return builder.as_markup()


def get_delete_product_kb():
    """Клавиатура для удаления товаров"""
    builder = InlineKeyboardBuilder()

    # Создаем кнопки для каждой категории
    for category in products.keys():
        builder.button(text=f"🗑️ {category}", callback_data=f"delete_category_{category}")

    builder.button(text="📋 Список товаров", callback_data="admin_list_products")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_products_to_delete_kb(category):
    """Клавиатура с товарами для удаления"""
    builder = InlineKeyboardBuilder()

    if category in products:
        for product in products[category]:
            builder.button(
                text=f"❌ {product['name']} - {product['price']} руб.",
                callback_data=f"delete_product_{category}_{product['id']}"
            )

    builder.button(text="⬅️ Назад", callback_data="admin_delete_product")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    # Инициализируем корзину для пользователя, если её нет
    if user_id not in user_carts:
        user_carts[user_id] = []

    await message.answer(
        f"👋 Добро пожаловать в <b>KiLoKSS69★</b>!\n"
        f"Здесь ты можешь заказать крутой мерч с доставкой по СНГ.\n\n"
        f"Выберите раздел:",
        reply_markup=get_main_menu(user_id),
        parse_mode='HTML'
    )


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели")
        return

    await message.answer(
        "👨‍💻 <b>Админ-панель KiLoKSS69★</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_menu(),
        parse_mode='HTML'
    )


# ==================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ====================

@dp.message(F.text == "Каталог товаров")
async def show_categories_handler(message: types.Message):
    await show_categories(message)


@dp.message(F.text.startswith("Карзина"))
async def show_cart_handler(message: types.Message):
    await show_cart(message)


@dp.message(F.text == "Мои заказы")
async def show_orders_handler(message: types.Message):
    await show_orders(message)


@dp.message(F.text == "Контакты")
async def show_contacts_handler(message: types.Message):
    await show_contacts(message)


@dp.message(F.text == "Акции")
async def show_promotions_handler(message: types.Message):
    await show_promotions(message)


# ==================== ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ ====================

@dp.message(F.text == "👨‍💻 Админ-панель")
async def admin_panel_handler(message: types.Message):
    await cmd_admin(message)


@dp.message(F.text == "📦 Управление товарами")
async def manage_products_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🛍️ <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_products_management_kb(),
        parse_mode='HTML'
    )


@dp.message(F.text == "📊 Статистика")
async def show_stats_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    total_orders = sum(len(orders) for orders in user_orders.values())
    total_users = len(user_carts)

    # Подсчет по статусам
    status_stats = {}
    total_revenue = 0

    for user_orders_list in user_orders.values():
        for order in user_orders_list:
            status = order.get('status', 'new')
            status_stats[status] = status_stats.get(status, 0) + 1
            if status != 'cancelled':
                total_revenue += order.get('total', 0)

    # Подсчет товаров в корзинах
    total_in_carts = 0
    for cart in user_carts.values():
        total_in_carts += len(cart)

    stats_text = (
        "📊 <b>Статистика магазина</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"📦 Всего заказов: <b>{total_orders}</b>\n"
        f"💰 Выручка: <b>{total_revenue} руб.</b>\n\n"
        f"<b>Статусы заказов:</b>\n"
    )

    for status_key, status_name in ORDER_STATUSES.items():
        count = status_stats.get(status_key, 0)
        stats_text += f"• {status_name}: <b>{count}</b>\n"

    stats_text += f"\n🛒 Товаров в корзинах: <b>{total_in_carts}</b>\n"
    stats_text += f"🆔 ID администратора: <code>{message.from_user.id}</code>"

    await message.answer(stats_text, parse_mode='HTML')


@dp.message(F.text == "📋 Все заказы")
async def show_all_orders_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await show_all_orders_admin(message)


# ==================== ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ СТАТУСАМИ ЗАКАЗОВ ====================

async def show_all_orders_admin(message: types.Message, status_filter=None):
    """Показать все заказы с фильтрацией по статусу"""
    if not is_admin(message.from_user.id):
        return

    if not any(user_orders.values()):
        await message.answer("📦 Заказов пока нет")
        return

    orders_text = "📦 <b>Все заказы:</b>\n\n"
    order_count = 0

    for user_id, user_orders_list in user_orders.items():
        for order in user_orders_list:
            # Фильтрация по статусу
            if status_filter and order.get('status') != status_filter:
                continue

            order_count += 1
            current_status = ORDER_STATUSES.get(order.get('status', 'new'), '🆕 Новый')

            orders_text += f"🆔 <b>Заказ №{order['id']}</b>\n"
            orders_text += f"📊 Статус: {current_status}\n"
            orders_text += f"👤 ФИО: {order.get('customer_name', 'Не указано')}\n"
            orders_text += f"📞 Телефон: {order.get('customer_phone', 'Не указан')}\n"
            orders_text += f"📍 Адрес: {order.get('customer_address', 'Не указан')}\n"
            orders_text += f"💰 Сумма: {order['total']} руб.\n"
            orders_text += f"📅 Дата: {order.get('date', 'Не указана')}\n"

            orders_text += "<b>Товары:</b>\n"
            for item in order['items']:
                orders_text += f"• {item['name']} ({item['size']}) - {item['quantity']}шт.\n"

            orders_text += f"\n🛠 <b>Изменить статус:</b> /status_{order['id']}\n"
            orders_text += "─" * 30 + "\n\n"

    if order_count == 0:
        status_name = ORDER_STATUSES.get(status_filter, 'выбранному статусу')
        await message.answer(f"📦 Заказов со статусом '{status_name}' нет")
        return

    await message.answer(
        orders_text,
        parse_mode='HTML',
        reply_markup=get_order_management_kb()
    )


async def show_order_details_admin(message: types.Message, order_id: int):
    """Показать детали заказа для админа"""
    order = None
    user_id_for_order = None

    for user_id, user_orders_list in user_orders.items():
        for ord in user_orders_list:
            if ord['id'] == order_id:
                order = ord
                user_id_for_order = user_id
                break
        if order:
            break

    if not order:
        await message.answer("❌ Заказ не найден")
        return

    current_status = ORDER_STATUSES.get(order.get('status', 'new'), '🆕 Новый')

    order_text = f"📋 <b>Детали заказа №{order['id']}</b>\n\n"
    order_text += f"📊 <b>Текущий статус:</b> {current_status}\n"
    order_text += f"👤 <b>Клиент:</b> {order.get('customer_name', 'Не указано')}\n"
    order_text += f"📞 <b>Телефон:</b> {order.get('customer_phone', 'Не указан')}\n"
    order_text += f"📍 <b>Адрес:</b> {order.get('customer_address', 'Не указан')}\n"
    order_text += f"🚚 <b>Доставка:</b> {order.get('shipping_method', 'Не указана')}\n"
    order_text += f"💳 <b>Оплата:</b> {order.get('payment_method', 'Не указана')}\n"
    order_text += f"💰 <b>Сумма:</b> {order['total']} руб.\n"
    order_text += f"📅 <b>Дата:</b> {order.get('date', 'Не указана')}\n\n"

    order_text += "<b>Товары:</b>\n"
    for item in order['items']:
        order_text += f"• {item['name']} ({item['size']}) - {item['quantity']}шт. | {item['price']} руб.\n"

    await message.answer(
        order_text,
        parse_mode='HTML',
        reply_markup=get_order_management_kb(order_id)
    )


async def update_order_status(order_id: int, new_status: str, admin_id: int):
    """Обновить статус заказа и уведомить пользователя"""
    order = None
    user_id_for_order = None

    for user_id, user_orders_list in user_orders.items():
        for ord in user_orders_list:
            if ord['id'] == order_id:
                order = ord
                user_id_for_order = user_id
                break
        if order:
            break

    if not order:
        return False

    old_status = order.get('status', 'new')
    order['status'] = new_status
    order['status_updated'] = datetime.now().strftime("%d.%m.%Y %H:%M")
    order['updated_by_admin'] = admin_id

    # Сохраняем изменения
    save_data()

    # Уведомляем пользователя об изменении статуса
    status_name = ORDER_STATUSES.get(new_status, 'Новый')
    old_status_name = ORDER_STATUSES.get(old_status, 'Новый')

    try:
        await bot.send_message(
            user_id_for_order,
            f"📦 <b>Статус вашего заказа №{order_id} изменен</b>\n\n"
            f"🔄 Было: {old_status_name}\n"
            f"✅ Стало: {status_name}\n\n"
            f"Для подробностей используйте раздел \"Мои заказы\"",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Не удалось уведомить пользователя {user_id_for_order}: {e}")

    return True


# ==================== CALLBACK ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ ====================

@dp.callback_query(F.data.startswith('admin_'))
async def handle_admin_callbacks(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    if callback.data == "admin_menu":
        await state.clear()
        await callback.message.answer(
            "👨‍💻 Админ-панель",
            reply_markup=get_admin_menu()
        )

    elif callback.data == "admin_add_product":
        await callback.message.answer(
            "➕ <b>Добавление нового товара</b>\n\n"
            "Введите название товара:",
            parse_mode='HTML'
        )
        await state.set_state(AdminState.waiting_for_product_name)

    elif callback.data == "admin_delete_product":
        await show_delete_products_menu(callback.message)

    elif callback.data == "admin_list_products":
        await show_products_list(callback.message)

    elif callback.data == "admin_products_stats":
        total_products = sum(len(category) for category in products.values())
        total_categories = len(products)

        stats_text = (
            "📊 <b>Статистика товаров</b>\n\n"
            f"📦 Всего товаров: <b>{total_products}</b>\n"
            f"📂 Категорий: <b>{total_categories}</b>\n"
        )

        for category, category_products in products.items():
            stats_text += f"• {category}: {len(category_products)} товаров\n"

        await callback.message.answer(stats_text, parse_mode='HTML')

    elif callback.data == "admin_all_orders":
        await show_all_orders_admin(callback.message)

    elif callback.data == "admin_new_orders":
        await show_all_orders_admin(callback.message, "new")

    elif callback.data == "admin_shipping_orders":
        await show_all_orders_admin(callback.message, "shipped")

    elif callback.data.startswith("admin_category_"):
        category = callback.data.replace("admin_category_", "")
        await state.update_data(product_category=category)
        await state.set_state(AdminState.waiting_for_product_sizes)
        await callback.message.answer(
            "📏 Введите доступные размеры через запятую (например: S,M,L,XL):"
        )

    elif callback.data == "admin_new_category":
        await callback.message.answer("📝 Введите название новой категории:")
        await state.set_state(AdminState.waiting_for_product_category)

    await callback.answer()


@dp.callback_query(F.data.startswith('set_status_'))
async def handle_set_status_callback(callback: types.CallbackQuery):
    """Обработчик изменения статуса заказа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    parts = callback.data.split('_')
    if len(parts) >= 4:
        order_id = int(parts[2])
        new_status = parts[3]

        if await update_order_status(order_id, new_status, callback.from_user.id):
            status_name = ORDER_STATUSES.get(new_status, 'Неизвестный')
            await callback.message.answer(
                f"✅ Статус заказа №{order_id} изменен на: {status_name}",
                reply_markup=get_order_management_kb()
            )
        else:
            await callback.message.answer(
                "❌ Не удалось изменить статус заказа",
                reply_markup=get_order_management_kb()
            )

    await callback.answer()


# ==================== КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ СТАТУСАМИ ====================

@dp.message(F.text.startswith("/status_"))
async def handle_status_command(message: types.Message):
    """Обработчик команды для изменения статуса заказа"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде")
        return

    try:
        order_id = int(message.text.replace("/status_", ""))
        await show_order_details_admin(message, order_id)
    except ValueError:
        await message.answer("❌ Неверный формат команды. Используйте: /status_123")


# ==================== ОСТАЛЬНЫЕ ФУНКЦИИ (без изменений) ====================

@dp.message(F.text == "👤 Обычное меню")
async def back_to_user_menu(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        "Обычное меню:",
        reply_markup=get_main_menu(user_id)
    )


# ... (остальные функции без изменений - handle_delete_callbacks, handle_user_navigation,
# handle_cart_callbacks, handle_order_callbacks, show_delete_products_menu,
# show_products_to_delete, delete_product, show_categories, show_cart, show_product,
# start_checkout, process_shipping, process_payment, confirm_order, edit_order,
# process_name, process_phone, process_address, show_products_list,
# process_product_name, process_product_description, process_product_price,
# process_new_category, process_product_sizes, process_product_photo)

# ==================== ОБНОВЛЕННАЯ ФУНКЦИЯ ПОКАЗА ЗАКАЗОВ ====================

async def show_orders(message: types.Message):
    user_id = message.from_user.id
    orders = user_orders.get(user_id, [])

    if not orders:
        await message.answer(
            "📦 У вас еще нет заказов\n\n"
            "Сделайте ваш первый заказ через каталог товаров!",
            reply_markup=get_main_menu(user_id)
        )
        return

    orders_text = "📦 <b>Ваши заказы:</b>\n\n"

    for order in reversed(orders):  # Показываем новые заказы первыми
        current_status = ORDER_STATUSES.get(order.get('status', 'new'), '🆕 Новый')

        orders_text += f"📋 <b>Заказ №{order['id']}</b>\n"
        orders_text += f"📅 Дата: {order['date']}\n"
        orders_text += f"💰 Сумма: {order['total']} руб.\n"
        orders_text += f"📊 Статус: {current_status}\n"

        if order.get('status_updated'):
            orders_text += f"🕒 Обновлен: {order['status_updated']}\n"

        orders_text += f"🚚 Доставка: {order['shipping_method']}\n"
        orders_text += f"💳 Оплата: {order['payment_method']}\n\n"

        orders_text += "<b>Товары:</b>\n"
        for item in order['items']:
            orders_text += f"• {item['name']} ({item['size']}) - {item['quantity']}шт.\n"

        orders_text += "\n" + "─" * 30 + "\n\n"

    await message.answer(orders_text, parse_mode='HTML', reply_markup=get_main_menu(user_id))


# ==================== ОБНОВЛЕННАЯ ФУНКЦИЯ ПОДТВЕРЖДЕНИЯ ЗАКАЗА ====================

async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    global order_counter

    user_id = callback.from_user.id
    data = await state.get_data()
    cart = data['cart']

    total = sum(item["price"] * item["quantity"] for item in cart)
    order_id = order_counter
    order_counter += 1

    # Сохраняем заказ
    if user_id not in user_orders:
        user_orders[user_id] = []

    user_orders[user_id].append({
        "id": order_id,
        "items": cart.copy(),
        "total": total,
        "customer_name": data['customer_name'],
        "customer_phone": data['customer_phone'],
        "customer_address": data['customer_address'],
        "shipping_method": data['shipping_method'],
        "payment_method": data['payment_method'],
        "status": "new",  # Статус по умолчанию
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    })

    # Очищаем корзину
    user_carts[user_id] = []

    # Сохраняем данные
    save_data()

    await state.clear()

    await callback.message.answer(
        f"✅ <b>Спасибо! Ваш заказ №{order_id} принят!</b>\n\n"
        f"💰 Сумма заказа: {total} руб.\n"
        f"🚚 Способ доставки: {data['shipping_method']}\n"
        f"💳 Способ оплаты: {data['payment_method']}\n"
        f"📊 Статус: {ORDER_STATUSES['new']}\n\n"
        f"📞 В ближайшее время с вами свяжется менеджер для уточнения деталей.\n\n"
        f"Для отслеживания статуса заказа используйте раздел \"Мои заказы\"",
        reply_markup=get_main_menu(user_id),
        parse_mode='HTML'
    )

    # Уведомляем админов о новом заказе
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 <b>НОВЫЙ ЗАКАЗ №{order_id}</b>\n\n"
                f"👤 Клиент: {data['customer_name']}\n"
                f"📞 Телефон: {data['customer_phone']}\n"
                f"💰 Сумма: {total} руб.\n\n"
                f"Для управления: /status_{order_id}",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Не удалось уведомить админа {admin_id}: {e}")


# ... (остальные функции без изменений - show_contacts, show_promotions, cmd_myid)

# Запуск бота
async def main():
    logging.info("Бот KiLoKSS69★ запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())