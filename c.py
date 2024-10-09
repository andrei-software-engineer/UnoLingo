from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import requests
import sqlite3

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')

# Database setup
def init_db():
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    # Create rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_name) REFERENCES rooms (name)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

rooms = {}

def validate_token(token):
    """ Validate the JWT token by sending a request to the authentication service. """
    try:
        response = requests.get('http://localhost:3000/gateway/validate_token', headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            return response.json()  # Return the JSON response if the token is valid
        return None  # Return None if the token is invalid
    except requests.exceptions.RequestException as e:
        print(f"Token validation error: {e}")
        return None

def save_message(room_name, username, message):
    """ Save the message to the database. """
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (room_name, username, message) VALUES (?, ?, ?)', (room_name, username, message))
    conn.commit()
    conn.close()

@socketio.on('joinRoom')
def handle_join_room(data):
    token = data.get('token')
    room_name = data.get('room')

    user_info = validate_token(token)
    if user_info is None:
        send('Invalid token. You cannot join the room.', room=request.sid)
        return

    username = user_info['user']['username']  # Extract username from the token validation response
    if room_name not in rooms:
        rooms[room_name] = []
    rooms[room_name].append(request.sid)
    send(f'Joined room: {room_name} as {username}', room=request.sid)

@socketio.on('message')
def handle_message(data):
    token = data.get('token')
    room = data.get('room')
    msg = data.get('message')

    user_info = validate_token(token)
    if user_info is None:
        send('Invalid token. You cannot send messages.', room=request.sid)
        return

    username = user_info['user']['username']  # Extract username from the token validation response

    if room in rooms and request.sid in rooms[room]:
        formatted_message = f"{username}: {msg}"  # Format message with username
        save_message(room, username, msg)  # Save the message to the database
        for user in rooms[room]:
            emit("message", formatted_message, room=user)  # Send the message to the specified room
    else:
        send('You are not in this room.', room=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
