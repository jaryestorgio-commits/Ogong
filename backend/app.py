from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import hashlib
import hmac
import secrets
from config import DB_CONFIG

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)


def rows_to_list(rows):
    return [dict(row) for row in rows]


@app.route('/test_db')
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = cur.fetchall()
        conn.close()
        return jsonify({"status": "success", "tables": [row[0] for row in tables]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.errorhandler(404)
def handle_404(error):
    if request.path.startswith('/api/'):
        return jsonify({'message': 'Not Found'}), 404
    return app.send_static_file('index.html')


def get_connection():
    conn = sqlite3.connect(DB_CONFIG['database'], timeout=DB_CONFIG.get('timeout', 30))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@app.errorhandler(sqlite3.Error)
def handle_db_error(error):
    return jsonify({'message': 'Database connection failed. Check SQLite database and backend config.', 'error': str(error)}), 500


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return f'pbkdf2_sha256$600000${salt}${digest}'


def verify_password(password, stored_password):
    if stored_password.startswith('pbkdf2_sha256$'):
        try:
            _, iterations, salt, expected_digest = stored_password.split('$', 3)
            actual_digest = hashlib.pbkdf2_hmac(
                'sha256', password.encode(), salt.encode(), int(iterations)
            ).hex()
            return hmac.compare_digest(actual_digest, expected_digest)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(stored_password, password)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, username, role, password FROM users WHERE username=?', (username,))
        user = cursor.fetchone()
        if not user or not verify_password(password, user['password']):
            return jsonify({'message': 'Invalid credentials.'}), 401
        return jsonify({
            'id': user['id'],
            'name': user['name'],
            'username': user['username'],
            'role': user['role']
        })
    finally:
        conn.close()


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not all([name, username, email, password]):
        return jsonify({'message': 'Full name, username, email, and password are required.'}), 400
    if '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
        return jsonify({'message': 'Please enter a valid email address.'}), 400
    if len(password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        columns = {row['name'] for row in cursor.execute('PRAGMA table_info(users)')}
        if 'email' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
        cursor.execute('SELECT 1 FROM users WHERE username=? OR lower(email)=?', (username, email))
        if cursor.fetchone():
            return jsonify({'message': 'Username or email already exists.'}), 409
        cursor.execute(
            'INSERT INTO users (name, username, email, password, role) VALUES (?, ?, ?, ?, ?)',
            (name, username, email, hash_password(password), 'STAFF')
        )
        conn.commit()
        return jsonify({'message': 'Account created successfully.'}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'message': 'Username or email already exists.'}), 409
    finally:
        conn.close()


@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, username, role FROM users ORDER BY id')
        users = cursor.fetchall()
        return jsonify(rows_to_list(users))
    finally:
        conn.close()


@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json or {}
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not all([name, username, password, role]):
        return jsonify({'message': 'All fields are required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)',
            (name, username, password, role)
        )
        conn.commit()
        return jsonify({'message': 'User created.'}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'message': 'Username already exists.'}), 400
    finally:
        conn.close()


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json or {}
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not all([name, username, role]):
        return jsonify({'message': 'Name, username, and role are required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        if password:
            cursor.execute(
                'UPDATE users SET name=?, username=?, password=?, role=? WHERE id=?',
                (name, username, password, role, user_id)
            )
        else:
            cursor.execute(
                'UPDATE users SET name=?, username=?, role=? WHERE id=?',
                (name, username, role, user_id)
            )
        conn.commit()
        return jsonify({'message': 'User updated.'})
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'message': 'Username already exists.'}), 400
    finally:
        conn.close()


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
        conn.commit()
        return jsonify({'message': 'User deleted.'})
    finally:
        conn.close()


@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, category_name FROM categories ORDER BY id')
        categories = cursor.fetchall()
        return jsonify(rows_to_list(categories))
    finally:
        conn.close()


@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json or {}
    category_name = data.get('category_name')
    if not category_name:
        return jsonify({'message': 'Category name is required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (category_name) VALUES (?)', (category_name,))
        conn.commit()
        return jsonify({'message': 'Category created.'}), 201
    finally:
        conn.close()


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.json or {}
    category_name = data.get('category_name')
    if not category_name:
        return jsonify({'message': 'Category name is required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE categories SET category_name=? WHERE id=?', (category_name, category_id))
        conn.commit()
        return jsonify({'message': 'Category updated.'})
    finally:
        conn.close()


@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE id=?', (category_id,))
        conn.commit()
        return jsonify({'message': 'Category deleted.'})
    finally:
        conn.close()


@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, supplier_name, contact_person, phone, email, address FROM suppliers ORDER BY id')
        suppliers = cursor.fetchall()
        return jsonify(rows_to_list(suppliers))
    finally:
        conn.close()


@app.route('/api/suppliers', methods=['POST'])
def create_supplier():
    data = request.json or {}
    supplier_name = data.get('supplier_name')
    contact_person = data.get('contact_person')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')
    if not supplier_name:
        return jsonify({'message': 'Supplier name is required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO suppliers (supplier_name, contact_person, phone, email, address) VALUES (?, ?, ?, ?, ?)',
            (supplier_name, contact_person, phone, email, address)
        )
        conn.commit()
        return jsonify({'message': 'Supplier created.'}), 201
    finally:
        conn.close()


@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    data = request.json or {}
    supplier_name = data.get('supplier_name')
    contact_person = data.get('contact_person')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')
    if not supplier_name:
        return jsonify({'message': 'Supplier name is required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE suppliers SET supplier_name=?, contact_person=?, phone=?, email=?, address=? WHERE id=?',
            (supplier_name, contact_person, phone, email, address, supplier_id)
        )
        conn.commit()
        return jsonify({'message': 'Supplier updated.'})
    finally:
        conn.close()


@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM suppliers WHERE id=?', (supplier_id,))
        conn.commit()
        return jsonify({'message': 'Supplier deleted.'})
    finally:
        conn.close()


@app.route('/api/products', methods=['GET'])
def get_products():
    search = request.args.get('search', '')
    conn = get_connection()

    try:
        cursor = conn.cursor()
        query = '''
            SELECT
                p.id,
                p.product_name,
                c.category_name,
                s.supplier_name,
                p.price,
                p.cost,
                p.stock_quantity,
                p.reorder_level,
                p.created_at
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN suppliers s ON p.supplier_id = s.id
        '''
        params = []

        if search:
            query += '''
                WHERE
                    p.product_name LIKE ?
                    OR c.category_name LIKE ?
                    OR s.supplier_name LIKE ?
            '''
            term = f'%{search}%'
            params = [term, term, term]

        cursor.execute(query, params)
        products = cursor.fetchall()
        return jsonify(rows_to_list(products))
    finally:
        conn.close()


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                p.id,
                p.product_name,
                p.category_id,
                p.supplier_id,
                c.category_name,
                s.supplier_name,
                p.price,
                p.cost,
                p.stock_quantity,
                p.reorder_level,
                p.created_at
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
        ''', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'message': 'Product not found.'}), 404
        return jsonify(dict(product))
    finally:
        conn.close()


@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json or {}
    product_name = data.get('product_name')
    category_id = data.get('category_id')
    supplier_id = data.get('supplier_id')
    price = data.get('price')
    cost = data.get('cost')
    stock_quantity = data.get('stock_quantity')
    reorder_level = data.get('reorder_level')

    if not all([product_name, category_id, supplier_id, price is not None, cost is not None, stock_quantity is not None]):
        return jsonify({'message': 'Product name, category, supplier, price, cost, and stock quantity are required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (
                product_name,
                category_id,
                supplier_id,
                price,
                cost,
                stock_quantity,
                reorder_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_name, category_id, supplier_id, price, cost, stock_quantity, reorder_level or 0))
        conn.commit()
        return jsonify({'message': 'Product created.'}), 201
    finally:
        conn.close()


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json or {}
    product_name = data.get('product_name')
    category_id = data.get('category_id')
    supplier_id = data.get('supplier_id')
    price = data.get('price')
    cost = data.get('cost')
    stock_quantity = data.get('stock_quantity')
    reorder_level = data.get('reorder_level')

    if not all([product_name, category_id, supplier_id, price is not None, cost is not None, stock_quantity is not None]):
        return jsonify({'message': 'Product name, category, supplier, price, cost, and stock quantity are required.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products
            SET
                product_name = ?,
                category_id = ?,
                supplier_id = ?,
                price = ?,
                cost = ?,
                stock_quantity = ?,
                reorder_level = ?
            WHERE id = ?
        ''', (product_name, category_id, supplier_id, price, cost, stock_quantity, reorder_level or 0, product_id))
        conn.commit()
        return jsonify({'message': 'Product updated.'})
    finally:
        conn.close()


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        return jsonify({'message': 'Product deleted.'})
    finally:
        conn.close()


@app.route('/api/sales', methods=['GET'])
def get_sales():
    search = request.args.get('search', '')
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = '''
            SELECT
                sa.id,
                sa.invoice_number,
                sa.sale_date,
                u.name AS cashier,
                sa.total_amount,
                sa.payment_method
            FROM sales sa
            JOIN users u ON sa.user_id = u.id
        '''
        params = []
        if search:
            query += '''
                WHERE
                    sa.invoice_number LIKE ?
                    OR u.name LIKE ?
                    OR sa.payment_method LIKE ?
            '''
            term = f'%{search}%'
            params = [term, term, term]
        query += ' ORDER BY sa.sale_date DESC'
        cursor.execute(query, params)
        sales = cursor.fetchall()
        return jsonify(rows_to_list(sales))
    finally:
        conn.close()


@app.route('/api/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                sa.id,
                sa.invoice_number,
                sa.sale_date,
                sa.total_amount,
                sa.payment_method,
                sa.amount_received,
                sa.change_amount,
                u.name AS cashier
            FROM sales sa
            JOIN users u ON sa.user_id = u.id
            WHERE sa.id = ?
        ''', (sale_id,))
        sale = cursor.fetchone()
        if not sale:
            return jsonify({'message': 'Sale not found.'}), 404

        sale = dict(sale)
        cursor.execute('''
            SELECT
                si.id,
                si.product_id,
                p.product_name,
                si.quantity,
                si.price,
                si.cost,
                si.subtotal,
                (si.price - si.cost) AS profit_per_item,
                ((si.price - si.cost) * si.quantity) AS total_profit
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        ''', (sale_id,))
        items = rows_to_list(cursor.fetchall())
        total_cost = 0
        total_profit = 0

        for item in items:
            item_cost = float(item['cost']) * int(item['quantity'])
            item['total_cost'] = item_cost
            total_cost += item_cost
            total_profit += float(item['total_profit'])

        sale['items'] = items
        sale['total_cost'] = total_cost
        sale['gross_profit'] = total_profit
        return jsonify(sale)
    finally:
        conn.close()


@app.route('/api/sales', methods=['POST'])
def create_sale():
    data = request.json or {}
    user_id = data.get('user_id')
    payment_method = data.get('payment_method')
    amount_received = data.get('amount_received')
    current_transaction = data.get('current_transaction')

    if not all([user_id, payment_method, current_transaction]) or not isinstance(current_transaction, list):
        return jsonify({'message': 'Invalid sale data.'}), 400
    if len(current_transaction) == 0:
        return jsonify({'message': 'Current transaction is empty.'}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        validated_items = []

        for item in current_transaction:
            if not all([item.get('product_id'), item.get('quantity'), item.get('price')]):
                conn.rollback()
                return jsonify({'message': 'Invalid line item.'}), 400

            cursor.execute('''
                SELECT id, product_name, price, cost, stock_quantity
                FROM products
                WHERE id = ?
            ''', (item['product_id'],))
            product = cursor.fetchone()
            if not product:
                conn.rollback()
                return jsonify({'message': f"Product id {item['product_id']} not found."}), 404

            quantity = int(item['quantity'])
            if quantity > product['stock_quantity']:
                conn.rollback()
                return jsonify({'message': f"Insufficient stock for {product['product_name']}"}), 400

            selling_price = float(product['price'])
            product_cost = float(product['cost'])
            subtotal = round(selling_price * quantity, 2)
            validated_items.append({
                'product_id': product['id'],
                'product_name': product['product_name'],
                'quantity': quantity,
                'price': selling_price,
                'cost': product_cost,
                'subtotal': subtotal
            })

        total_amount = sum(item['subtotal'] for item in validated_items)
        cursor.execute('SELECT COUNT(*) AS count FROM sales')
        count = cursor.fetchone()['count'] or 0
        invoice_number = f'INV-{count + 1:06d}'

        change_amount = None
        if payment_method == 'Cash':
            if amount_received is None:
                conn.rollback()
                return jsonify({'message': 'Amount received is required for cash payments.'}), 400
            amount_received = float(amount_received)
            if amount_received < total_amount:
                conn.rollback()
                return jsonify({'message': 'Amount received is less than total amount.'}), 400
            change_amount = round(amount_received - total_amount, 2)
        else:
            amount_received = None
            change_amount = 0

        cursor.execute('''
            INSERT INTO sales (
                invoice_number,
                user_id,
                total_amount,
                payment_method,
                amount_received,
                change_amount
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (invoice_number, user_id, total_amount, payment_method, amount_received, change_amount))
        sale_id = cursor.lastrowid

        for item in validated_items:
            cursor.execute('''
                INSERT INTO sale_items (
                    sale_id,
                    product_id,
                    quantity,
                    price,
                    cost,
                    subtotal
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (sale_id, item['product_id'], item['quantity'], item['price'], item['cost'], item['subtotal']))
            cursor.execute('''
                UPDATE products
                SET stock_quantity = stock_quantity - ?
                WHERE id = ?
            ''', (item['quantity'], item['product_id']))

        conn.commit()
        return jsonify({'message': 'Sale completed.', 'invoice_number': invoice_number, 'sale_id': sale_id, 'total_amount': total_amount}), 201
    except Exception as exc:
        conn.rollback()
        return jsonify({'message': 'Failed to complete sale.', 'error': str(exc)}), 500
    finally:
        conn.close()


@app.route('/api/reports', methods=['GET'])
def get_reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    conn = get_connection()
    try:
        cursor = conn.cursor()
        date_condition = ''
        params = []
        if start_date and end_date:
            date_condition = 'WHERE DATE(sa.sale_date) BETWEEN ? AND ?'
            params = [start_date, end_date]

        summary_query = f'''
            SELECT
                COUNT(sa.id) AS transaction_count,
                COALESCE(SUM(sa.total_amount), 0) AS total_sales
            FROM sales sa
            {date_condition}
        '''
        cursor.execute(summary_query, params)
        totals = dict(cursor.fetchone())
        total_sales = float(totals['total_sales'] or 0)
        transaction_count = int(totals['transaction_count'] or 0)

        cost_query = '''
            SELECT COALESCE(SUM(p.cost * si.quantity), 0) AS total_cost
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales sa ON si.sale_id = sa.id
        '''
        cost_params = []
        if start_date and end_date:
            cost_query += ' WHERE DATE(sa.sale_date) BETWEEN ? AND ?'
            cost_params = [start_date, end_date]
        cursor.execute(cost_query, cost_params)
        cost_result = dict(cursor.fetchone())
        total_cost = float(cost_result['total_cost'] or 0)

        total_profit = total_sales - total_cost
        average_sale = total_sales / transaction_count if transaction_count > 0 else 0

        best_sellers_query = '''
            SELECT
                p.product_name,
                SUM(si.quantity) AS total_quantity,
                COALESCE(SUM(si.subtotal), 0) AS total_sales,
                COALESCE(SUM(si.subtotal - (p.cost * si.quantity)), 0) AS total_profit
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales sa ON si.sale_id = sa.id
        '''
        best_seller_params = []
        if start_date and end_date:
            best_sellers_query += ' WHERE DATE(sa.sale_date) BETWEEN ? AND ?'
            best_seller_params = [start_date, end_date]
        best_sellers_query += ' GROUP BY si.product_id, p.product_name ORDER BY total_quantity DESC LIMIT 5'
        cursor.execute(best_sellers_query, best_seller_params)
        best_sellers = rows_to_list(cursor.fetchall())

        cursor.execute('''
            SELECT id, product_name, stock_quantity, reorder_level
            FROM products
            WHERE stock_quantity <= reorder_level
            ORDER BY stock_quantity ASC
            LIMIT 10
        ''')
        low_stock = rows_to_list(cursor.fetchall())

        return jsonify({
            'transaction_count': transaction_count,
            'total_sales': total_sales,
            'total_cost': total_cost,
            'total_profit': total_profit,
            'gross_profit': total_profit,
            'average_sale': average_sale,
            'best_sellers': best_sellers,
            'low_stock': low_stock
        })
    except Exception as exc:
        print('REPORT ERROR:', str(exc))
        return jsonify({'message': 'Unable to generate report.', 'error': str(exc)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
