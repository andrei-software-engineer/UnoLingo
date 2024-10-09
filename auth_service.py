# Service A (auth_service.py)

from flask import Flask, jsonify, request
import jwt
import datetime
import sqlite3

app = Flask(__name__)

SECRET_KEY = '2222'

def init_db():
    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Register new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

    return jsonify({"message": f"User {username} registered successfully!"}), 201

# Login and issue JWT token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        token = jwt.encode({
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY)
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Check service status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Service A (Authentication) is up"}), 200

# Validate JWT token from Authorization header
@app.route('/validate_token', methods=['GET'])
def validate_token():
    auth_header = request.headers.get('Authorization')
    print(auth_header)
    
    if not auth_header:
        return jsonify({"error": "Authorization header is missing!"}), 400

    token = auth_header.split(" ")[1] if " " in auth_header else None

    if not token:
        return jsonify({"error": "Token is missing!"}), 400

    try:
        # Decode the token to validate it
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({"message": "Token is valid!", "user": decoded}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired!"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token!"}), 401

if __name__ == "__main__":
    app.run(port=5003)
