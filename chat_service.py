from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import requests
import sqlite3
import socket

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
        CREATE TABLE IF NOT EXISTS lobby (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT UNIQUE NOT NULL
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
            FOREIGN KEY (room_name) REFERENCES lobby (room_name)
        )
    ''')
    # Create users in rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_in_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            user_sid TEXT NOT NULL,
            UNIQUE(room_name, user_sid)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

def save_room(room_name):
    """ Save the room to the database. """
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO lobby (room_name) VALUES (?)', (room_name,))
    conn.commit()
    conn.close()

def add_user_to_room(room_name, user_sid):
    """ Add a user to a room in the database. """
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users_in_rooms (room_name, user_sid) VALUES (?, ?)', (room_name, user_sid))
    conn.commit()
    conn.close()

def remove_user_from_room(room_name, user_sid):
    """ Remove a user from a room in the database. """
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users_in_rooms WHERE room_name = ? AND user_sid = ?', (room_name, user_sid))
    conn.commit()
    conn.close()

def is_user_in_room(room_name, user_sid):
    """ Check if a user is in a room. """
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_sid FROM users_in_rooms WHERE room_name = ? AND user_sid = ?', (room_name, user_sid))
    user_exists = cursor.fetchone() is not None
    conn.close()
    return user_exists

@socketio.on('createRoom')
def handle_create_room(data):
    room_name = data.get('room')
    
    # Create room if it doesn't exist in the database
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    
    try:
        save_room(room_name)  # Save the new room in the database
        send(f'Room "{room_name}" created.', room=request.sid)
    except sqlite3.IntegrityError:
        send(f'Room "{room_name}" already exists.', room=request.sid)
    
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
    
    # Check if the room exists in the database
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT room_name FROM lobby WHERE room_name = ?', (room_name,))
    room_exists = cursor.fetchone() is not None
    conn.close()

    if not room_exists:
        send(f'Room "{room_name}" does not exist.', room=request.sid)
        return

    # Add the user to the room in the database
    add_user_to_room(room_name, request.sid)
    send(f'Joined room: {room_name} as {username}', room=request.sid)

@socketio.on('leaveRoom')
def handle_leave_room(data):
    room_name = data.get('room')
    
    # Remove the user from the room in the database
    remove_user_from_room(room_name, request.sid)
    send(f'You left room: {room_name}', room=request.sid)

@socketio.on('getRooms')
def handle_get_rooms(data):
    """Fetch the list of rooms from the database and send it to the client."""
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    
    # Query the database for all room names
    cursor.execute('SELECT room_name FROM lobby')
    rooms_in_db = cursor.fetchall()
    
    # Extract room names from the query result
    room_list = [room[0] for room in rooms_in_db]
    
    conn.close()
    
    # Send the room list to the user who requested it
    emit('message', room_list, room=request.sid)

@socketio.on('getRoomMessages')
def handle_get_room_messages(data):
    room_name = data.get('room')
    
    # Fetch messages from the database
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, message FROM messages WHERE room_name = ? ORDER BY timestamp DESC LIMIT 100', (room_name,))
    messages = [f"{row[0]}: {row[1]}" for row in cursor.fetchall()]
    emit('message', messages, room=request.sid)
    conn.close()

@socketio.on('deleteRoom')
def handle_delete_room(data):
    room_name = data.get('room')
    
    conn = sqlite3.connect('chat_service.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lobby WHERE room_name = ?', (room_name,))
    conn.commit()
    conn.close()

    send(f'Room "{room_name}" deleted.', room=request.sid)

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

    # Check if the user is in the room
    if not is_user_in_room(room, request.sid):
        send('You are not in this room.', room=request.sid)
        return

    # Save the message to the database
    formatted_message = f"{username}: {msg}"  # Format message with username
    save_message(room, username, msg)  # Save the message to the database
    emit("message", formatted_message, broadcast=True)  # Send the message to all users

if __name__ == "__main__":
    init_db()

    import argparse
    parser = argparse.ArgumentParser(description='Flask Application')
    parser.add_argument('-p', '--port', required=True, help='port of the service')
    
    args = parser.parse_args()
    socketio.run(app, debug=True, port=args.port)
