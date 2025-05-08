from flask import Flask, request, jsonify, render_template, redirect, flash, url_for, session
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash

print("✅ app.py is executing")

app = Flask(__name__)
app.secret_key = 'd591b7aba2ca5559c1c2ba7de51c0dde'
CORS(app)

db = mysql.connector.connect(
    host='localhost', user='root', password='Wriksen@012', database='boutique_db'
)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home')
def home():
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        print(products)
        return render_template('home.html', products=products)
    finally:
        cursor.close()


@app.route('/orders')
def orders():
    customer_id = request.args.get('customer_id')
    if not customer_id:
        return "User not logged in", 401

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                o.order_id,
                o.order_date,
                o.status,
                oi.product_id,
                p.name AS product_name,
                p.price AS product_price,
                oi.quantity,
                o.total_amount
            FROM Orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN Products p ON oi.product_id = p.product_id
            WHERE o.customer_id = %s
            ORDER BY o.order_date DESC
        """, (customer_id,))
        orders = cursor.fetchall()

        # Group orders by individual order item
        individual_orders = []
        for order in orders:
            individual_orders.append(order)

        return render_template('orders.html', orders=individual_orders)
    finally:
        cursor.close()


@app.route('/cart')
def cart():
    customer_id = request.args.get('customer_id')

    if not customer_id:
        return "User not logged in", 401

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.product_id,
                p.name,
                p.price,
                p.image_url,
                oi.quantity
            FROM
                order_items oi
            JOIN
                products p ON oi.product_id = p.product_id
            WHERE
                oi.customer_id = %s AND oi.order_id IS NULL
        """, (customer_id,))

        products = cursor.fetchall()
        print(f"Products in cart for user {customer_id}: {products}")
        return render_template('cart.html', products=products)
    finally:
        cursor.close()


@app.route("/contact")
def contact():
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM employees")
        employees = cursor.fetchall()
        return render_template("contact.html", employees=employees)
    finally:
        cursor.close()


@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
                            (name, email, message))
        db.commit()
        flash("Thank you for contacting us! We'll get back to you soon.")
        return redirect("/contact")
    finally:
        cursor.close()


@app.route('/addToCart', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data['product_id']
    quantity = int(data.get('quantity', 1))
    customer_id = data.get('customer_id')

    if not customer_id:
        return jsonify({'error': 'customer_id is required.'}), 400

    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT * FROM order_items WHERE product_id = %s AND customer_id = %s AND order_id IS NULL",
            (product_id, customer_id)
        )
        existing_item = cursor.fetchone()

        if existing_item:
            cursor.execute(
                "UPDATE order_items SET quantity = quantity + %s WHERE product_id = %s AND customer_id = %s AND order_id IS NULL",
                (quantity, product_id, customer_id)
            )
        else:
            cursor.execute(
                "INSERT INTO order_items (product_id, customer_id, quantity, order_id) VALUES (%s, %s, %s, NULL)",
                (product_id, customer_id, quantity)
            )

        db.commit()
        return jsonify({
            'message': f'Product {product_id} added to cart with quantity {quantity} for customer {customer_id}.'
        }), 200
    finally:
        cursor.close()


@app.route('/getCartItems', methods=['GET'])
def get_cart_items():
    customer_id = request.args.get('customer_id')
    if not customer_id or not customer_id.isdigit():
        return jsonify({"error": "Invalid or missing customer_id"}), 400

    customer_id = int(customer_id)
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT products.product_id, products.name, products.price, products.image_url, order_items.quantity
            FROM order_items
            JOIN products ON order_items.product_id = products.product_id
            WHERE order_items.customer_id = %s AND order_items.order_id IS NULL
        """, (customer_id,))
        cart_items = cursor.fetchall()
        return jsonify(cart_items)
    finally:
        cursor.close()


@app.route('/removeFromCart', methods=['POST'])
def remove_from_cart():
    data = request.json
    print(data)
    product_id = data.get('product_id')
    customer_id = data.get('customer_id')

    if not product_id or not customer_id:
        return jsonify({'error': 'product_id and customer_id are required.'}), 400

    cursor = db.cursor()
    try:
        cursor.execute(
            "DELETE FROM order_items WHERE product_id = %s AND customer_id = %s AND order_id IS NULL",
            (product_id, customer_id)
        )
        db.commit()
        return jsonify({'message': f'Product {product_id} removed from cart for customer {customer_id}.'}), 200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({'error': f'Database error: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {e}'}), 500
    finally:
        cursor.close()


@app.route('/checkout', methods=['POST'])
def checkout():
    customer_id = request.json.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'customer_id is required.'}), 400

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host='localhost', user='root', password='Wriksen@012', database='boutique_db'
        )
        cursor = conn.cursor()
        conn.start_transaction()

        # 1. Get items from the "cart" (order_items with order_id IS NULL)
        cursor.execute("""
            SELECT product_id, quantity
            FROM order_items
            WHERE customer_id = %s AND order_id IS NULL
        """, (customer_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            conn.rollback()
            return jsonify({'message': 'Your cart is empty.'}), 200

        # 2. Process each item in the cart and create a new order
        for product_id, quantity in cart_items:
            # Get the product price
            cursor.execute("SELECT price FROM Products WHERE product_id = %s", (product_id,))
            product_data = cursor.fetchone()
            if product_data:
                price = product_data[0]
                total_amount = price * quantity

                # Insert a new order for each item
                cursor.execute("""
                    INSERT INTO Orders (customer_id, order_date, total_amount, status)
                    VALUES (%s, NOW(), %s, 'Order Placed')
                """, (customer_id, total_amount))
                order_id = cursor.lastrowid  # Correct way to get the last inserted ID

                # Update the corresponding order_item with the new order_id
                cursor.execute("""
                    UPDATE order_items
                    SET order_id = %s
                    WHERE customer_id = %s AND product_id = %s AND order_id IS NULL
                    LIMIT 1  -- Important to update only the current cart item
                """, (order_id, customer_id, product_id))

            else:
                conn.rollback()
                return jsonify({'error': f'Product with ID {product_id} not found.'}), 404

        # 3. Clear the cart (remove any remaining order_items with order_id IS NULL)
        cursor.execute("""
            DELETE FROM order_items
            WHERE customer_id = %s AND order_id IS NULL
        """, (customer_id,))

        # Commit the transaction
        conn.commit()

        return jsonify({'message': 'Order(s) placed successfully!'}), 200

    except mysql.connector.Error as err:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify({'error': f'Database error during checkout: {err}'}), 500
    except Exception as e:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify({'error': f'Server error during checkout: {e}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@app.route('/getEmployees', methods=['GET'])
def get_employees():
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM employees")
        employees = cursor.fetchall()
        return jsonify(employees), 200
    finally:
        cursor.close()


@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data['name']
        phone = data['phone']
        email = data['email']
        address = data['address']
        password = generate_password_hash(data['password'])

        cursor = db.cursor()
        try:
            cursor.execute(
                'SELECT * FROM customers WHERE email = %s OR phone = %s', (email, phone)
            )
            if cursor.fetchone():
                return jsonify({'message': 'User already exists! Try logging in.'}), 400

            cursor.execute(
                'INSERT INTO customers (name, email, phone, address, password) VALUES (%s, %s, %s, %s, %s)',
                (name, email, phone, address, password)
            )

            db.commit()
            return jsonify({'message': 'Sign-up successful! Now log in.'}), 201
        finally:
            cursor.close()
    except Exception as e:
        print('Error:', e)
        return jsonify({'message': 'An error occurred during signup!'}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    identifier = data['identifier']

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT * FROM customers WHERE email = %s OR phone = %s',
            (identifier, identifier)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({'message': 'User not found! Please sign up.'}), 404
        else:
            customer_id = user['customer_id']
            name = user['name']
            return jsonify({'customer_id': customer_id, 'message': f"Welcome, {name}! Login successful."}), 200
    finally:
        cursor.close()


if __name__ == "__main__":
    app.run(debug=True)
