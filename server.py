import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = 'swiftcash.db'
ADMIN_EMAIL = "junaidshah78634@gmail.com" # Setting you as the default admin

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Transactions table with status for withdrawals
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            amount INTEGER,
            type TEXT,
            description TEXT,
            status TEXT DEFAULT 'completed',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    # Add status column if it doesn't exist (migration)
    try:
        conn.execute('ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT "completed"')
    except:
        pass

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
        user_data = {'email': email, 'name': name, 'points': 0, 'is_admin': (email == ADMIN_EMAIL)}
    else:
        user_data = dict(user)
        user_data['is_admin'] = (email == ADMIN_EMAIL)
        
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
    conn.execute('INSERT INTO transactions (user_email, amount, type, description, status) VALUES (?, ?, ?, ?, ?)', 
                 (email, amount, 'earn', desc, 'completed'))
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
        conn.execute('INSERT INTO transactions (user_email, amount, type, description, status) VALUES (?, ?, ?, ?, ?)', 
                     (email, -amount_points, 'withdraw', f'Withdrawal to {upi_id}', 'pending'))
        conn.commit()
        status = 'success'
        message = 'Withdrawal request submitted'
    else:
        status = 'error'
        message = 'Insufficient points'
        
    conn.close()
    return jsonify({'status': status, 'message': message})

@app.route('/api/transactions/<email>', methods=['GET'])
def get_transactions(email):
    conn = get_db_connection()
    txs = conn.execute('SELECT * FROM transactions WHERE user_email = ? ORDER BY timestamp DESC LIMIT 20', (email,)).fetchall()
    conn.close()
    return jsonify([dict(tx) for tx in txs])

# --- Admin Routes ---

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    data = request.json
    email = data.get('email')
    if email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_points = conn.execute('SELECT SUM(points) FROM users').fetchone()[0] or 0
    pending_withdrawals = conn.execute('SELECT COUNT(*) FROM transactions WHERE type="withdraw" AND status="pending"').fetchone()[0]
    
    conn.close()
    return jsonify({
        'total_users': total_users,
        'total_points': total_points,
        'pending_withdrawals': pending_withdrawals
    })

@app.route('/api/admin/users', methods=['POST'])
def admin_users():
    data = request.json
    email = data.get('email')
    if email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY last_login DESC').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/transactions', methods=['POST'])
def admin_transactions():
    data = request.json
    email = data.get('email')
    if email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    txs = conn.execute('SELECT * FROM transactions ORDER BY timestamp DESC').fetchall()
    conn.close()
    return jsonify([dict(tx) for tx in txs])

@app.route('/api/admin/update-tx', methods=['POST'])
def update_transaction():
    data = request.json
    admin_email = data.get('admin_email')
    tx_id = data.get('tx_id')
    new_status = data.get('status') # 'completed' or 'rejected'

    if admin_email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    conn.execute('UPDATE transactions SET status = ? WHERE id = ?', (new_status, tx_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
