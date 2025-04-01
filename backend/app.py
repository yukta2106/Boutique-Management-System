from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host='localhost', user='root', password='Wriksen012@', database='boutique_db'
)
cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data['name']
        phone = data['phone']
        email = data['email']
        address = data['address']
        password = generate_password_hash(data['password'])

        cursor.execute(
            'SELECT * FROM customers WHERE email = %s OR phone = %s', (email, phone)
        )
        if cursor.fetchone():
            return jsonify({'message': 'User already exists! Try logging in.'}), 400
        cursor.execute(
            'INSERT INTO customers (name, phone, email, address, password) VALUES (%s, %s, %s, %s, %s)',
            (name, phone, email, address, password)
        )
        db.commit()

        return jsonify({'message': 'Sign-up successful! Now log in.'}), 201
    except Exception as e:
        return jsonify({'message': 'An error occurred during signup!', 'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    identifier = data['identifier']

    cursor.execute(
        'SELECT * FROM customers WHERE email = %s OR phone = %s',
        (identifier, identifier)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'User not found! Please sign up.'}), 404
    return jsonify({'message': f"Welcome, {user[1]}! Login successful."}), 200

@app.route('/inventory', methods=['GET'])
def get_inventory_status():
    try:
        cursor.execute("SELECT * FROM InventoryStatus")
        inventory = cursor.fetchall()
        result = []
        for row in inventory:
            result.append({
                "product_id": row[0],
                "name": row[1],
                "stock": row[2],
                "stock_status": row[3]
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": "Error fetching inventory!", "error": str(e)}), 500

@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        data = request.json
        customer_id = data['customer_id']
        total_amount = data['total_amount']
        
        cursor.execute("INSERT INTO Orders (customer_id, total_amount) VALUES (%s, %s)", (customer_id, total_amount))
        order_id = cursor.lastrowid
        
        for item in data['items']:
            product_id = item['product_id']
            quantity = item['quantity']
            price = item['price']
            
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)", 
                           (order_id, product_id, quantity, price))
        
        cursor.execute("CALL ProcessOrder(%s)", (order_id,))
        
        db.commit()
        return jsonify({"message": "Order placed successfully!", "order_id": order_id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"message": "Order placement failed!", "error": str(e)}), 500

@app.route('/restock', methods=['POST'])
def create_restock_order():
    try:
        data = request.json
        product_id = data['product_id']
        supplier_id = data['supplier_id']
        quantity = data['quantity']
        
        cursor.execute("INSERT INTO RestockOrders (product_id, supplier_id, quantity) VALUES (%s, %s, %s)", 
                       (product_id, supplier_id, quantity))
        
        db.commit()
        return jsonify({"message": "Restock order placed successfully!"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"message": "Failed to place restock order!", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
