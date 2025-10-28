import sqlite3
import json


class Database:
    def __init__(self, db_name='@KiLoKSS69_bot'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()


        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                category TEXT,
                sizes TEXT,
                photo TEXT,
                is_available BOOLEAN DEFAULT TRUE
            )
        ''')

        # Таблица корзины
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                size TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                items TEXT,
                total_amount INTEGER,
                status TEXT DEFAULT 'pending',
                customer_name TEXT,
                customer_phone TEXT,
                customer_address TEXT,
                shipping_method TEXT,
                payment_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')


        self.add_sample_products(cursor)

        conn.commit()
        conn.close()

    def add_sample_products(self, cursor):
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('Зипка с болоклавой', ' черная толстовка с капюшоном, '
                                       'полностью застёгнутая на молнию. Капюшон также закрывает лицо, создавая загадочный образ. На левой стороне груди имеется яркий декоративный элемент: красные пятна, напоминающие брызги краски или крови, а поверх них белая надпись в стиле граффити "KLOKSS 89" и звёздочка. Фон изображения чёрный, что подчёркивает мрачный, уличный стиль этой одежды.', 2500, 'Футболки', 'S,M,L,XL',
                 'картинка')
            ]

            cursor.executemany('''
                INSERT INTO products (name, description, price, category, sizes, photo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', sample_products)

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def add_user(self, user_id, username, full_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, full_name))
        conn.commit()
        conn.close()

    def get_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM products WHERE is_available = 1')
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def get_products_by_category(self, category):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE category = ? AND is_available = 1', (category,))
        products = cursor.fetchall()
        conn.close()
        return products

    def get_product(self, product_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product

    def add_to_cart(self, user_id, product_id, size, quantity=1):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cart (user_id, product_id, size, quantity)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, size, quantity))
        conn.commit()
        conn.close()

    def get_cart(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, p.name, p.price, c.quantity, c.size, p.id as product_id
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        cart_items = cursor.fetchall()
        conn.close()
        return cart_items

    def get_cart_count(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(quantity) FROM cart WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0] or 0
        conn.close()
        return count

    def clear_cart(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def remove_from_cart(self, cart_item_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE id = ?', (cart_item_id,))
        conn.commit()
        conn.close()

    def create_order(self, user_id, items, total_amount, customer_name, customer_phone, customer_address,
                     shipping_method, payment_method):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, items, total_amount, customer_name, customer_phone, customer_address, shipping_method, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, json.dumps(items), total_amount, customer_name, customer_phone, customer_address,
              shipping_method, payment_method))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def get_user_orders(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, total_amount, status, created_at
            FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        orders = cursor.fetchall()
        conn.close()
        return orders