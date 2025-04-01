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
        print('Error:', e)
        return jsonify({'message': 'An error occurred during signup!'}), 500


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


if __name__ == '__main__':
    app.run(debug=True)
