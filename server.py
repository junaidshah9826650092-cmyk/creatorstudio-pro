import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Local disk storage disabled (Cloud Only)

# Load .env manually for local development
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'vitox.db')
ADMIN_EMAIL = "junaidshah78634@gmail.com" 

# PostgreSQL or SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    # Fix Render's postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print(f"Using PostgreSQL: {DATABASE_URL[:30]}...")
else:
    print(f"Using SQLite: {DB_FILE}")

_db_ready = False

def get_db_connection():
    global _db_ready
    if not _db_ready:
        init_db()
        _db_ready = True
    
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    print(f"--- INITIALIZING DATABASE AT {DB_FILE} ---")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
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
            likes INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    # Subscriptions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscriber_email TEXT,
            channel_email TEXT,
            PRIMARY KEY (subscriber_email, channel_email)
        )
    ''')
    # Video Likes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS video_likes (
            user_email TEXT,
            video_id INTEGER,
            PRIMARY KEY (user_email, video_id)
        )
    ''')
    # Comments table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            user_email TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos (id)
        )
    ''')

    # Video Views
    conn.execute('''
        CREATE TABLE IF NOT EXISTS video_views (
            video_id INTEGER,
            user_email TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (video_id, user_email)
        )
    ''')

    # Add columns if they don't exist (migrations)
    try:
        conn.execute('ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT "completed"')
    except: pass
    try:
        conn.execute('ALTER TABLE videos ADD COLUMN likes INTEGER DEFAULT 0')
    except: pass

    conn.commit()
    conn.close()
    print("Database Initialized Successfully.")

# Run DB Init immediately on load (needed for Gunicorn/Render)
init_db()

# --- Serve Static Files ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt')

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"status": "error", "message": "Internal Server Error", "details": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"status": "error", "message": str(e)}), 500

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

# Local file storage has been decommissioned in favor of Cloud Storage (Firebase/Cloudinary).

@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
            
        email = data.get('email')
        title = data.get('title')
        desc = data.get('description', '')
        video_url = data.get('video_url')
        thumb_url = data.get('thumbnail_url', '')
        
        if not email or not title or not video_url:
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400
            
        conn = get_db_connection()
        # Double check if table exists as fallback
        try:
            conn.execute('SELECT 1 FROM videos LIMIT 1')
        except sqlite3.OperationalError:
            print("Fallback: Table 'videos' missing in route. Re-init...")
            init_db()

        conn.execute('INSERT INTO videos (user_email, title, description, video_url, thumbnail_url) VALUES (?, ?, ?, ?, ?)', 
                     (email, title, desc, video_url, thumb_url))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Upload Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

# --- ENGAGEMENT API ---

@app.route('/api/user/liked-videos/<email>', methods=['GET'])
def get_liked_videos(email):
    conn = get_db_connection()
    try:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT v.id, v.title, v.description, v.video_url, v.timestamp, v.views, v.user_email
                FROM videos v
                JOIN video_likes l ON v.id = l.video_id
                WHERE l.user_email = %s
                ORDER BY v.timestamp DESC
            ''', (email,))
            videos = cursor.fetchall()
        else:
            videos = conn.execute('''
                SELECT v.id, v.title, v.description, v.video_url, v.timestamp, v.views, v.user_email
                FROM videos v
                JOIN video_likes l ON v.id = l.video_id
                WHERE l.user_email = ?
                ORDER BY v.timestamp DESC
            ''', (email,)).fetchall()
            videos = [dict(row) for row in videos]
        
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/video/view', methods=['POST'])
def increment_view():
    data = request.json
    video_id = data.get('video_id')
    user_email = data.get('email')

    conn = get_db_connection()
    
    # Unique View Logic
    if user_email:
        # Check if user already viewed this video
        existing = conn.execute('SELECT 1 FROM video_views WHERE video_id = ? AND user_email = ?', (video_id, user_email)).fetchone()
        if existing:
            conn.close()
            return jsonify({'status': 'already_viewed'})
        
        # Record new view
        conn.execute('INSERT INTO video_views (video_id, user_email) VALUES (?, ?)', (video_id, user_email))

    conn.execute('UPDATE videos SET views = views + 1 WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/video/like', methods=['POST'])
def like_video():
    data = request.json
    video_id = data.get('video_id')
    email = data.get('email')
    
    conn = get_db_connection()
    already_liked = conn.execute('SELECT 1 FROM video_likes WHERE user_email = ? AND video_id = ?', (email, video_id)).fetchone()
    
    if already_liked:
        conn.execute('DELETE FROM video_likes WHERE user_email = ? AND video_id = ?', (email, video_id))
        conn.execute('UPDATE videos SET likes = likes - 1 WHERE id = ?', (video_id,))
        status = 'unliked'
    else:
        conn.execute('INSERT INTO video_likes (user_email, video_id) VALUES (?, ?)', (email, video_id))
        conn.execute('UPDATE videos SET likes = likes + 1 WHERE id = ?', (video_id,))
        status = 'liked'
    
    conn.commit()
    likes = conn.execute('SELECT likes FROM videos WHERE id = ?', (video_id,)).fetchone()['likes']
    conn.close()
    return jsonify({'status': status, 'likes': likes})

@app.route('/api/channel/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    subscriber = data.get('subscriber')
    channel = data.get('channel')
    
    conn = get_db_connection()
    already_subbed = conn.execute('SELECT 1 FROM subscriptions WHERE subscriber_email = ? AND channel_email = ?', (subscriber, channel)).fetchone()
    
    if already_subbed:
        conn.execute('DELETE FROM subscriptions WHERE subscriber_email = ? AND channel_email = ?', (subscriber, channel))
        status = 'unsubscribed'
    else:
        conn.execute('INSERT INTO subscriptions (subscriber_email, channel_email) VALUES (?, ?)', (subscriber, channel))
        status = 'subscribed'
    
    conn.commit()
    count = conn.execute('SELECT COUNT(*) FROM subscriptions WHERE channel_email = ?', (channel,)).fetchone()[0]
    conn.close()
    return jsonify({'status': status, 'subscribers': count})

@app.route('/api/video/comment', methods=['POST'])
def add_comment():
    data = request.json
    video_id = data.get('video_id')
    email = data.get('email')
    content = data.get('content')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO comments (video_id, user_email, content) VALUES (?, ?, ?)', (video_id, email, content))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/video/comments/<video_id>', methods=['GET'])
def get_comments(video_id):
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments WHERE video_id = ? ORDER BY timestamp DESC', (video_id,)).fetchall()
    conn.close()
    return jsonify([dict(c) for c in comments])

@app.route('/api/video/stats/<video_id>', methods=['POST'])
def get_video_stats(video_id):
    email = request.json.get('email', '')
    conn = get_db_connection()
    vid = conn.execute('SELECT views, likes FROM videos WHERE id = ?', (video_id,)).fetchone()
    liked = conn.execute('SELECT 1 FROM video_likes WHERE user_email = ? AND video_id = ?', (email, video_id)).fetchone()
    subbed = False
    if email:
        channel_email = conn.execute('SELECT user_email FROM videos WHERE id = ?', (video_id,)).fetchone()['user_email']
        subbed = conn.execute('SELECT 1 FROM subscriptions WHERE subscriber_email = ? AND channel_email = ?', (email, channel_email)).fetchone() is not None
        subs_count = conn.execute('SELECT COUNT(*) FROM subscriptions WHERE channel_email = ?', (channel_email,)).fetchone()[0]
    else:
        subs_count = 0

    comment_count = conn.execute('SELECT COUNT(*) FROM comments WHERE video_id = ?', (video_id,)).fetchone()[0]
    conn.close()
    return jsonify({
        'views': vid['views'],
        'likes': vid['likes'],
        'liked': liked is not None,
        'subbed': subbed,
        'subscribers': subs_count,
        'comment_count': comment_count
    })

# --- Admin/Stats Routes ---

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
    video_stats = conn.execute('SELECT COUNT(*) as count, SUM(views) as total_views FROM videos WHERE user_email = ?', (email,)).fetchone()
    total_videos = video_stats['count'] if video_stats['count'] else 0
    total_views = video_stats['total_views'] if video_stats['total_views'] else 0
    subs_count = conn.execute('SELECT COUNT(*) FROM subscriptions WHERE channel_email = ?', (email,)).fetchone()[0]
    
    conn.close()
    return jsonify({
        'subscribers': subs_count, 
        'views': total_views,
        'watch_time': 0,
        'video_count': total_videos
    })
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

@app.route('/api/debug/db', methods=['GET'])
def debug_db():
    try:
        conn = get_db_connection()
        tables = conn.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
        table_list = [t[0] for t in tables]
        conn.close()
        return jsonify({"status": "ok", "tables": table_list, "db_path": DB_FILE})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

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

@app.route('/api/admin/delete-video', methods=['POST'])
def delete_video():
    data = request.json
    admin_email = data.get('admin_email')
    video_id = data.get('video_id')

    if admin_email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM videos WHERE id = %s', (video_id,))
        else:
            conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/video/delete', methods=['POST'])
def creator_delete_video():
    data = request.json
    user_email = data.get('email')
    video_id = data.get('video_id')

    conn = get_db_connection()
    
    # Verify ownership
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('SELECT user_email FROM videos WHERE id = %s', (video_id,))
        video = cursor.fetchone()
        owner = video['user_email'] if video else None
    else:
        video = conn.execute('SELECT user_email FROM videos WHERE id = ?', (video_id,)).fetchone()
        owner = video['user_email'] if video else None
    
    if not owner or owner != user_email:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Unauthorized or video not found'}), 403

    # Delete
    if USE_POSTGRES:
        cursor.execute('DELETE FROM videos WHERE id = %s', (video_id,))
    else:
        conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/ai/suggest', methods=['POST'])
def ai_suggest():
    data = request.json
    topic = data.get('topic', 'General Gaming')
    api_key = os.environ.get('GOOGLE_API_KEY', '').strip()
    
    if not api_key:
        print("API Key missing")
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

@app.route('/')
@app.route('/index.html')
def serve_index():
    from flask import make_response
    with open(os.path.join(BASE_DIR, 'index.html'), 'r', encoding='utf-8') as f:
        content = f.read()
    response = make_response(content)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Deploy ID: 1739556800
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
