from flask import Flask, jsonify, request
import requests
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('service_a.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)''')
    conn.commit()
    conn.close()

init_db()
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Service A is up"}), 200

@app.route('/communicate', methods=['GET'])
def communicate_with_b():
    try:
        response = requests.get('http://localhost:5001/message')
        return jsonify({"message_from_b": response.json()}), 200
    except requests.Timeout:
        return jsonify({"error": "Request to Service B timed out"}), 504

# Create a new user by accepting a POST request
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()  # Expecting JSON data like {"name": "John Doe"}
    name = data.get('name')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    # Insert the new user into the database
    conn = sqlite3.connect('service_a.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"User {name} created successfully!"}), 201


# List all users (optional, for testing purposes)
@app.route('/users', methods=['GET'])
def list_users():
    conn = sqlite3.connect('service_a.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    
    user_list = [{"id": user[0], "name": user[1]} for user in users]
    return jsonify(user_list), 200


if __name__ == "__main__":
    app.run(port=5002)
