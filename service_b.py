from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('service_b.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS learners (id INTEGER PRIMARY KEY, language_level TEXT)''')
    conn.commit()
    conn.close()

init_db()
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Service B is up"}), 200

@app.route('/message', methods=['GET'])
def message():
    return jsonify({"message": "Hello from Service B"}), 200
# Create a new learner by accepting a POST request
@app.route('/create_learner', methods=['POST'])

def create_learner():
    data = request.get_json()  # Expecting JSON data like {"language_level": "Beginner"}
    language_level = data.get('language_level')
    
    if not language_level:
        return jsonify({"error": "Language level is required"}), 400
    
    # Insert the new learner into the database
    conn = sqlite3.connect('service_b.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO learners (language_level) VALUES (?)', (language_level,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Learner with language level {language_level} created successfully!"}), 201

# List all learners (optional, for testing purposes)
@app.route('/learners', methods=['GET'])
def list_learners():
    conn = sqlite3.connect('service_b.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM learners')
    learners = cursor.fetchall()
    conn.close()
    
    learner_list = [{"id": learner[0], "language_level": learner[1]} for learner in learners]
    return jsonify(learner_list), 200


if __name__ == "__main__":
    app.run(port=5001)
