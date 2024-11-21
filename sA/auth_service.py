from flask import Flask, jsonify, request
import jwt
import datetime
import sqlite3
import socket
import signal
import sys
import os
import time
from prometheus_flask_exporter import PrometheusMetrics


app = Flask(__name__)

SECRET_KEY = '2222'

def init_db():
    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    # Update the users table to include a token column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, 
            username TEXT UNIQUE, 
            password TEXT, 
            token TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

metrics = PrometheusMetrics(app)


SERVICE_DISCOVERY_URL = "http://service-discovery:8080"
service_port = ModuleNotFoundError
import requests

def register_service():
    service_info = {
        'serviceName': 'auth_service',
        'serviceUrl': f"http://{service_port}:5003"  # Construct the service URL
    }

    try:
        response = requests.post(f"http://service-discovery:8080/register", json=service_info)
        if response.status_code == 200:
            print(f"Service auth_service registered successfully.")
        else:
            print(f"Failed to register service: {response.text}")
    except Exception as e:
        print(f"Error registering service: {e}")

def deregister_service():
    print("Deregistering service...")
    service_info = {
        'serviceName': 'auth_service',
        'serviceUrl': f"http://{service_port}:5003" 
    }

    try:
        response = requests.post(f"http://localhost:8080/deregister", json=service_info)
        if response.status_code == 200:
            print(f"Service {service_info['serviceName']} deregistered successfully.")
        else:
            print(f"Failed to deregister service: {response.text}")
    except Exception as e:
        print(f"Error deregistering service: {e}")


@app.route('/metrics')
def metrics():
    return metrics.registry.generate_latest()

# Register new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists!"}), 400
    finally:
        conn.close()

    return jsonify({"message": f"User {username} registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    # time.sleep(10)
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        if user:
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, SECRET_KEY)

            # Store token in the database
            cursor.execute('UPDATE users SET token = ? WHERE username = ?', (token, username))
            conn.commit()

            return jsonify({"token": token}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500  # Return database error
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return general error
    finally:
        conn.close()

# Validate JWT token from Authorization header
@app.route('/validate_token', methods=['GET'])
def validate_token():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({"error": "Authorization header is missing!"}), 400

    token = auth_header.split(" ")[1] if " " in auth_header else None

    if not token:
        return jsonify({"error": "Token is missing!"}), 400

    try:
        username = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])['username']
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired!"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token!"}), 401

    # Check if the token exists in the database
    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM users WHERE username = ?', (username,))
    db_token = cursor.fetchone()

    if db_token and db_token[0] == token:
        return jsonify({"message": "Token is valid!", "user": {"username": username}}), 200
    else:
        return jsonify({"error": "Token is not valid or expired!"}), 401

@app.route('/user/<id>', methods=['GET'])
def get_user(id):
    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username FROM users WHERE id = ?', (id,))
    user = cursor.fetchone()

    if user:
        return jsonify({"id": user[0], "username": user[1]}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Get all users
@app.route('/users', methods=['GET'])
def get_all_users():
    conn = sqlite3.connect('auth_service.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, username FROM users')
    users = cursor.fetchall()

    return jsonify([{"id": user[0], "username": user[1]} for user in users]), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Authentification service is running."}), 200 


# Signal handler function
def signal_handler(sig, frame):
    deregister_service()  # Call the deregistration function
    sys.exit(0)  # Exit the application

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Flask Application')
    parser.add_argument('-p', '--port', required=True, help='port of the service')

    args = parser.parse_args()
    service_port = args.port  # Store the port from args in the global variable

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    register_service()
    app.run(port=5003, host="0.0.0.0")