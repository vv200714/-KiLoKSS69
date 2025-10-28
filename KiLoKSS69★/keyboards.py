from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu():

    builder = ReplyKeyboardBuilder()


    builder.row(
        KeyboardButton(text="Каталог товаров"),
        KeyboardButton(text="Карзина")
    )
    builder.row(
        KeyboardButton(text="Мои заказы"),
        KeyboardButton(text="Контакты")
    )
    builder.row(
        KeyboardButton(text="Акции")
    )

    return builder.as_markup(resize_keyboard=True)


def get_categories_kb():
    from database import Database
    db = Database()
    categories = db.get_categories()

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category, callback_data=f"category_{category}")

    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_products_kb(category, product_index=0):
    from database import Database
    db = Database()
    products = db.get_products_by_category(category)

    if not products:
        return None

    product = products[product_index]
    sizes = product[4].split(',')

    builder = InlineKeyboardBuilder()


    for size in sizes:
        builder.button(text=size, callback_data=f"size_{product[0]}_{size}")


    nav_buttons = []
    if product_index > 0:
        builder.button(text="⬅️", callback_data=f"product_{category}_{product_index - 1}")

    builder.button(text="🛒 В корзину", callback_data="view_cart")

    if product_index < len(products) - 1:
        builder.button(text="➡️", callback_data=f"product_{category}_{product_index + 1}")

    builder.button(text="📂 В каталог", callback_data="back_to_categories")
    builder.adjust(3, 3, 2)
    return builder.as_markup()


def get_cart_kb(cart_items):
    builder = InlineKeyboardBuilder()

    for item in cart_items:
        cart_item_id, name, price, quantity, size, product_id = item
        builder.button(
            text=f"❌ {name} ({size}) - {quantity}шт.",
            callback_data=f"remove_{cart_item_id}"
        )

    if cart_items:
        builder.button(text="🧹 Очистить корзину", callback_data="clear_cart")
        builder.button(text="🚀 Оформить заказ", callback_data="checkout")

    builder.button(text="🛍️ Продолжить покупки", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


def get_shipping_methods_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📮 Почта России", callback_data="shipping_post")
    builder.button(text="🚚 СДЭК", callback_data="shipping_cdek")
    builder.button(text="🚗 Курьер", callback_data="shipping_courier")
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