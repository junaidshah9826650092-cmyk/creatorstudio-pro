import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = 'swiftcash.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            amount INTEGER,
            type TEXT,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    conn.commit()
    conn.close()

# --- Serve Static Files ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# --- API Routes ---
@app.route('/api/user', methods=['POST'])
def sync_user():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        conn.execute('INSERT INTO users (email, name, points) VALUES (?, ?, ?)', (email, name, 0))
        conn.commit()
        user_data = {'email': email, 'name': name, 'points': 0}
    else:
        user_data = dict(user)
        
    conn.close()
    return jsonify(user_data)

@app.route('/api/add-points', methods=['POST'])
def add_points():
    data = request.json
    email = data.get('email')
    amount = data.get('amount')
    desc = data.get('description', 'Task Completion')
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET points = points + ? WHERE email = ?', (amount, email))
    conn.execute('INSERT INTO transactions (user_email, amount, type, description) VALUES (?, ?, ?, ?)', 
                 (email, amount, 'earn', desc))
    conn.commit()
    
    new_points = conn.execute('SELECT points FROM users WHERE email = ?', (email,)).fetchone()['points']
    conn.close()
    
    return jsonify({'status': 'success', 'new_points': new_points})

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    email = data.get('email')
    amount_points = data.get('points')
    upi_id = data.get('upi_id')
    
    conn = get_db_connection()
    user = conn.execute('SELECT points FROM users WHERE email = ?', (email,)).fetchone()
    
    if user and user['points'] >= amount_points:
        conn.execute('UPDATE users SET points = points - ? WHERE email = ?', (amount_points, email))
        conn.execute('INSERT INTO transactions (user_email, amount, type, description) VALUES (?, ?, ?, ?)', 
                     (email, -amount_points, 'withdraw', f'Withdrawal to {upi_id}'))
        conn.commit()
        status = 'success'
        message = 'Withdrawal request submitted'
    else:
        status = 'error'
        message = 'Insufficient points'
        
    conn.close()
    return jsonify({'status': status, 'message': message})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
