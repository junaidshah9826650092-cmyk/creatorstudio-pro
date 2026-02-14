import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

# Load .env manually for local development
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = 'vitox.db'
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
            picture TEXT,
            points INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
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
    # Videos table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            title TEXT NOT NULL,
            description TEXT,
            video_url TEXT NOT NULL,
            thumbnail_url TEXT,
            views INTEGER DEFAULT 0,
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
    picture = data.get('picture', '')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        role = 'admin' if email == ADMIN_EMAIL else 'user'
        conn.execute('INSERT INTO users (email, name, picture, points, role) VALUES (?, ?, ?, ?, ?)', 
                     (email, name, picture, 0, role))
        conn.commit()
    else:
        # Update name/picture on login
        conn.execute('UPDATE users SET name = ?, picture = ?, last_login = CURRENT_TIMESTAMP WHERE email = ?', 
                     (name, picture, email))
        conn.commit()
    
    # Fetch updated user
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    user_data = dict(user)
    user_data['is_admin'] = (user['role'] == 'admin')
    
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

@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    data = request.json
    email = data.get('email')
    title = data.get('title')
    desc = data.get('description', '')
    video_url = data.get('video_url')
    thumb_url = data.get('thumbnail_url', '')
    
    if not email or not title or not video_url:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400
        
    conn = get_db_connection()
    conn.execute('INSERT INTO videos (user_email, title, description, video_url, thumbnail_url) VALUES (?, ?, ?, ?, ?)', 
                 (email, title, desc, video_url, thumb_url))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/videos', methods=['GET'])
def get_all_videos():
    conn = get_db_connection()
    videos = conn.execute('SELECT * FROM videos ORDER BY timestamp DESC').fetchall()
    conn.close()
    return jsonify([dict(v) for v in videos])

@app.route('/api/videos/<email>', methods=['GET'])
def get_user_videos(email):
    conn = get_db_connection()
    videos = conn.execute('SELECT * FROM videos WHERE user_email = ? ORDER BY timestamp DESC', (email,)).fetchall()
    conn.close()
    return jsonify([dict(v) for v in videos])

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

@app.route('/api/creator/stats', methods=['POST'])
def creator_stats():
    data = request.json
    email = data.get('email')
    
    conn = get_db_connection()
    # Mocking some creator-specific stats for now, but linked to real user points
    user = conn.execute('SELECT points FROM users WHERE email = ?', (email,)).fetchone()
    
    # In a real app, you'd have a 'videos' table with views/stats
    # For now we use real points to show the stack is working
    points = user['points'] if user else 0
    
    conn.close()
    return jsonify({
        'subscribers': points // 10, # Mocked ratio
        'views': points * 25,
        'watch_time': (points * 3) // 60
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

@app.route('/api/ai/suggest', methods=['POST'])
def ai_suggest():
    data = request.json
    topic = data.get('topic', 'General Gaming')
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        return jsonify({'error': 'AI API Key not configured'}), 500
        
    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Suggest a catchy YouTube title and a 2-sentence description for a video about: {topic}. Return JSON format with 'title' and 'description' keys. Do not include markdown formatting indicators."}]
            }]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        # Parse the response (Gemini returns a specific nested structure)
        text = result['candidates'][0]['content']['parts'][0]['text']
        # Clean up JSON if LLM added markdown
        import json
        import re
        clean_text = re.sub(r'```json\n?|\n?```', '', text).strip()
        suggestion = json.loads(clean_text)
        
        return jsonify(suggestion)
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({'title': f'Cool {topic} Video', 'description': f'An amazing video exploring {topic}. Check it out!'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
