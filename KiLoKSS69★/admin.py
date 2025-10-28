import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# States для админ-панели
class AdminState(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()
    waiting_for_product_sizes = State()
    waiting_for_product_photo = State()


# Загрузка данных
def load_data():
    if os.path.exists("bot_data.json"):
        with open("bot_data.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"carts": {}, "orders": {}, "order_counter": 1, "products": {}}


# Сохранение данных
def save_data(data):
    with open("bot_data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ID администраторов (замените на свои)
ADMIN_IDS = []  # Ваш Telegram ID


def is_admin(user_id):
    return user_id in ADMIN_IDS


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
    builder.button(text="➕ Добавить товар", callback_data="add_product")
    builder.button(text="📝 Редактировать товар", callback_data="edit_product")
    builder.button(text="🗑️ Удалить товар", callback_data="delete_product")
    builder.button(text="📋 Список товаров", callback_data="list_products")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_categories_kb_admin():
    builder = InlineKeyboardBuilder()
    categories = ["Футболки", "Худи", "Штаны", "Аксессуары", "Новая категория"]
    for category in categories:
        builder.button(text=category, callback_data=f"admin_category_{category}")
    builder.adjust(2)
    return builder.as_markup()


def get_orders_management_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Новые заказы", callback_data="new_orders")
    builder.button(text="📦 Все заказы", callback_data="all_orders")
    builder.button(text="✅ Завершенные", callback_data="completed_orders")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


# Команда для входа в админ-панель
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


# Управление товарами
async def manage_products(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🛍️ <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_products_management_kb(),
        parse_mode='HTML'
    )


# Статистика
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    total_orders = sum(len(orders) for orders in data.get("orders", {}).values())
    total_users = len(data.get("carts", {}))

    # Подсчет товаров в корзинах
    total_in_carts = 0
    for cart in data.get("carts", {}).values():
        total_in_carts += len(cart)

    stats_text = (
        "📊 <b>Статистика магазина</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"📦 Всего заказов: <b>{total_orders}</b>\n"
        f"🛒 Товаров в корзинах: <b>{total_in_carts}</b>\n"
        f"💰 Выручка: <b>рассчитывается...</b>\n\n"
        f"🆔 ID администратора: <code>{message.from_user.id}</code>"
    )

    await message.answer(stats_text, parse_mode='HTML')


# Показать все заказы
async def show_all_orders(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    orders = data.get("orders", {})

    if not any(orders.values()):
        await message.answer("📦 Заказов пока нет")
        return

    orders_text = "📦 <b>Все заказы:</b>\n\n"

    for user_id, user_orders in orders.items():
        for order in user_orders:
            orders_text += f"🆔 <b>Заказ №{order['id']}</b>\n"
            orders_text += f"👤 Пользователь: {user_id}\n"
            orders_text += f"📞 Телефон: {order.get('customer_phone', 'Не указан')}\n"
            orders_text += f"💰 Сумма: {order['total']} руб.\n"
            orders_text += f"📊 Статус: {order.get('status', 'В обработке')}\n"
            orders_text += f"📅 Дата: {order.get('date', 'Не указана')}\n"

            orders_text += "<b>Товары:</b>\n"
            for item in order['items']:
                orders_text += f"• {item['name']} ({item['size']}) - {item['quantity']}шт.\n"

            # Кнопки управления заказом
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Выполнен", callback_data=f"complete_order_{order['id']}_{user_id}")
            builder.button(text="❌ Отменить", callback_data=f"cancel_order_{order['id']}_{user_id}")
            builder.adjust(2)

            await message.answer(orders_text, reply_markup=builder.as_markup(), parse_mode='HTML')
            orders_text = "─" * 30 + "\n\n"


# Обработчики callback'ов для админ-панели
async def handle_admin_callbacks(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    data = load_data()

    if callback.data == "admin_menu":
        await callback.message.answer(
            "👨‍💻 Админ-панель",
            reply_markup=get_admin_menu()
        )

    elif callback.data == "add_product":
        await callback.message.answer(
            "Введите название товара:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        # Здесь нужно установить состояние ожидания данных товара

    elif callback.data.startswith("complete_order_"):
        parts = callback.data.split("_")
        order_id = int(parts[2])
        user_id = int(parts[3])

        # Обновляем статус заказа
        for uid, orders in data["orders"].items():
            if int(uid) == user_id:
                for order in orders:
                    if order["id"] == order_id:
                        order["status"] = "✅ Выполнен"
                        break
                break

        save_data(data)
        await callback.message.edit_text(f"✅ Заказ №{order_id} отмечен как выполненный")
        await callback.answer()

    elif callback.data.startswith("cancel_order_"):
        parts = callback.data.split("_")
        order_id = int(parts[2])
        user_id = int(parts[3])

        # Обновляем статус заказа
        for uid, orders in data["orders"].items():
            if int(uid) == user_id:
                for order in orders:
                    if order["id"] == order_id:
                        order["status"] = "❌ Отменен"
                        break
                break

        save_data(data)
        await callback.message.edit_text(f"❌ Заказ №{order_id} отменен")
        await callback.answer()

    await callback.answer()


# Добавьте в конец файла admin.py следующие функции:

def get_product_management_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить товар", callback_data="refresh_products")
    builder.button(text="📊 Статистика товаров", callback_data="products_stats")
    builder.button(text="🏠 Админ меню", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


async def add_product_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    await callback.message.answer(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Введите название товара:",
        parse_mode='HTML'
    )
    await state.set_state(AdminState.waiting_for_product_name)
    await callback.answer()


@dp.message(AdminState.waiting_for_product_name)
async def process_product_name(message: types.Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await state.set_state(AdminState.waiting_for_product_description)
    await message.answer("📝 Введите описание товара:")


@dp.message(AdminState.waiting_for_product_description)
async def process_product_description(message: types.Message, state: FSMContext):
    await state.update_data(product_description=message.text)
    await state.set_state(AdminState.waiting_for_product_price)
    await message.answer("💰 Введите цену товара (только цифры):")


@dp.message(AdminState.waiting_for_product_price)
async def process_product_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        await state.update_data(product_price=price)
        await state.set_state(AdminState.waiting_for_product_category)

        builder = InlineKeyboardBuilder()
        categories = ["Футболки", "Худи", "Штаны", "Аксессуары"]
        for category in categories:
            builder.button(text=category, callback_data=f"admin_category_{category}")
        builder.button(text="➕ Новая категория", callback_data="new_category")
        builder.adjust(2)

        await message.answer(
            "📂 Выберите категорию товара:",
            reply_markup=builder.as_markup()
        )
    except ValueError:
        await message.answer("❌ Введите корректную цену (только цифры):")


@dp.callback_query(AdminState.waiting_for_product_category)
async def process_product_category(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "new_category":
        await callback.message.answer("Введите название новой категории:")
        await state.set_state(AdminState.waiting_for_product_category)
    else:
        category = callback.data.replace("admin_category_", "")
        await state.update_data(product_category=category)
        await state.set_state(AdminState.waiting_for_product_sizes)
        await callback.message.answer(
            "📏 Введите доступные размеры через запятую (например: S,M,L,XL):"
        )
    await callback.answer()


@dp.message(AdminState.waiting_for_product_sizes)
async def process_product_sizes(message: types.Message, state: FSMContext):
    sizes = [size.strip() for size in message.text.split(",")]
    await state.update_data(product_sizes=sizes)
    await state.set_state(AdminState.waiting_for_product_photo)
    await message.answer("📸 Отправьте фото товара или введите URL:")


@dp.message(AdminState.waiting_for_product_photo)
async def process_product_photo(message: types.Message, state: FSMContext):
    photo_url = ""

    if message.photo:
        # Если отправлено фото, получаем file_id
        photo_url = message.photo[-1].file_id
    elif message.text and message.text.startswith("http"):
        # Если отправлен URL
        photo_url = message.text
    else:
        await message.answer("❌ Отправьте фото или корректный URL:")
        return

    # Получаем все данные
    data = await state.get_data()

    # Создаем новый товар
    new_product = {
        "id": len(products.get(data['product_category'], [])) + 1,
        "name": data['product_name'],
        "price": data['product_price'],
        "sizes": data['product_sizes'],
        "description": data['product_description'],
        "photo": photo_url,
        "details": "Добавлено через админ-панель"
    }

    # Добавляем товар в категорию
    if data['product_category'] not in products:
        products[data['product_category']] = []

    products[data['product_category']].append(new_product)

    # Сохраняем данные
    save_data({
        "carts": user_carts,
        "orders": user_orders,
        "order_counter": order_counter,
        "products": products
    })

    await message.answer(
        f"✅ <b>Товар успешно добавлен!</b>\n\n"
        f"📦 Название: {new_product['name']}\n"
        f"💰 Цена: {new_product['price']} руб.\n"
        f"📂 Категория: {data['product_category']}\n"
        f"📏 Размеры: {', '.join(new_product['sizes'])}",
        parse_mode='HTML',
        reply_markup=get_admin_menu()
    )

    await state.clear()


# Функция для отображения списка товаров
async def show_products_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    products_text = "📋 <b>Список товаров:</b>\n\n"

    for category, category_products in products.items():
        products_text += f"📂 <b>{category}</b>\n"
        for product in category_products:
            products_text += f"• {product['name']} - {product['price']} руб.\n"
        products_text += "\n"

    await message.answer(products_text, parse_mode='HTML', reply_markup=get_product_management_kb())


# Обработчики callback'ов для управления товарами
@dp.callback_query(F.data == "add_product")
async def add_product_callback(callback: types.CallbackQuery, state: FSMContext):
    await add_product_start(callback, state)


@dp.callback_query(F.data == "list_products")
async def list_products_callback(callback: types.CallbackQuery):
    await show_products_list(callback.message)
    await callback.answer()


@dp.callback_query(F.data == "refresh_products")
async def refresh_products_callback(callback: types.CallbackQuery):
    # Здесь можно добавить логику обновления списка товаров
    await callback.message.answer("🔄 Список товаров обновлен!")
    await show_products_list(callback.message)
    await callback.answer()


@dp.callback_query(F.data == "products_stats")
async def products_stats_callback(callback: types.CallbackQuery):
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
    await callback.answer()
