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
            'SELECT * FROM Customers WHERE email = %s OR phone = %s', (email, phone)
        )
        if cursor.fetchone():
            return jsonify({'message': 'User already exists! Try logging in.'}), 400
        
        # Call the AddCustomer stored procedure
        cursor.callproc('AddCustomer', (name, email, phone, address, password))
        db.commit()

        return jsonify({'message': 'Sign-up successful! Now log in.'}), 201
    except Exception as e:
        print('Error:', e)
        return jsonify({'message': 'An error occurred during signup!'}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    identifier = data['identifier']

    cursor.execute(
        'SELECT * FROM Customers WHERE email = %s OR phone = %s',
        (identifier, identifier)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'User not found! Please sign up.'}), 404
    return jsonify({'message': f"Welcome, {user[1]}! Login successful."}), 200


@app.route('/get_sales_report', methods=['GET'])
def get_sales_report():
    try:
        cursor.callproc('GetSalesReport')
        
        result = []
        for result_set in cursor.stored_results():
            result.append(result_set.fetchall())
        
        return jsonify({'sales_report': result}), 200
    except Exception as e:
        print('Error:', e)
        return jsonify({'message': 'An error occurred while fetching the sales report!'}), 500


if __name__ == '__main__':
    app.run(debug=True)
