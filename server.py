import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import base64

# Security & CSRF Protection
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_email = os.environ.get('ADMIN_EMAIL', 'junaidshah78634@gmail.com')
        # Simple header-based or param-based auth for demo, in prod use JWT
        auth_email = request.headers.get('X-Admin-Email')
        if auth_email != admin_email:
            return jsonify({'status': 'error', 'message': 'Administrative privileges required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Local disk storage disabled (Cloud Only)

# Load .env manually for local development
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from flask_talisman import Talisman

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
# Force HTTPS (Only on Render) and Security Headers
is_prod = os.environ.get('RENDER') == 'true'
Talisman(app, content_security_policy=None, force_https=is_prod)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'vitox.db')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'junaidshah78634@gmail.com')

# PostgreSQL or SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    # Fix Render's postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print(f"Using PostgreSQL: {DATABASE_URL[:30]}...")
else:
    print("---------------------------------------------------------")
    print("⚠️  WARNING: USING LOCAL SQLite STORAGE (EPHEMERAL)     ")
    if os.environ.get('RENDER') == 'true':
        print("⚠️  DANGER: DATA WILL BE DELETED ON EVERY REDEPLOY!    ")
        print("💡 FIX: Set DATABASE_URL in Render Dashboard.        ")
    print(f"Using SQLite: {DB_FILE}")
    print("---------------------------------------------------------")

_db_ready = False

def get_db_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        # Military-grade optimization for SQLite
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA synchronous = NORMAL')
        return conn

def to_json(data):
    """Helper to convert database results (with datetimes) to JSON serializable format."""
    from datetime import datetime, date
    if isinstance(data, list):
        return [to_json(i) for i in data]
    if isinstance(data, (dict, sqlite3.Row)) or (hasattr(data, 'items') and callable(getattr(data, 'items'))):
        d = dict(data)
        for k, v in d.items():
            if isinstance(v, (datetime, date)):
                d[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                d[k] = to_json(v)
        return d
    return data

def init_db():
    print(f"--- INITIALIZING MILITARY-GRADE DATABASE SYSTEM ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Unified SQL for both SQLite and PostgreSQL (using TEXT for simplicity)
    # Note: PostgreSQL uses SERIAL while SQLite uses AUTOINCREMENT
    id_type = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Users table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            picture TEXT,
            points INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            is_verified_brand BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS transactions (
            id {id_type},
            user_email TEXT,
            amount INTEGER,
            type TEXT,
            description TEXT,
            status TEXT DEFAULT 'completed',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Videos table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS videos (
            id {id_type},
            user_email TEXT,
            title TEXT NOT NULL,
            description TEXT,
            video_url TEXT NOT NULL,
            thumbnail_url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            type TEXT DEFAULT 'video',
            category TEXT DEFAULT 'All',
            moderation_status TEXT DEFAULT 'safe',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscriber_email TEXT,
            channel_email TEXT,
            PRIMARY KEY (subscriber_email, channel_email)
        )
    ''')
    
    # Video Likes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_likes (
            user_email TEXT,
            video_id TEXT,
            PRIMARY KEY (user_email, video_id)
        )
    ''')
    
    # Comments table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS comments (
            id {id_type},
            video_id TEXT,
            user_email TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Collaboration & Admin Messages table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS messages (
            id {id_type},
            sender_email TEXT,
            receiver_email TEXT,
            content TEXT,
            is_collab BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE
        )
    ''')

    # Community Posts Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS posts (
            id {id_type},
            user_email TEXT,
            content TEXT,
            image_url TEXT,
            likes INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Video Views
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_views (
            video_id TEXT,
            user_email TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (video_id, user_email)
        )
    ''')


    if not USE_POSTGRES:
        # SQLite migrations
        try: cursor.execute('ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT "completed"')
        except: pass
        try: cursor.execute('ALTER TABLE videos ADD COLUMN likes INTEGER DEFAULT 0')
        except: pass
        try: cursor.execute('ALTER TABLE videos ADD COLUMN type TEXT DEFAULT "video"')
        except: pass
        try: cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT "active"')
        except: pass
        try: cursor.execute('ALTER TABLE videos ADD COLUMN moderation_status TEXT DEFAULT "safe"')
        except: pass
    else:
        # Postgres migrations
        try: 
            cursor.execute('ALTER TABLE videos ADD COLUMN IF NOT EXISTS type TEXT DEFAULT \'video\'')
            cursor.execute('ALTER TABLE videos ADD COLUMN IF NOT EXISTS category TEXT DEFAULT \'All\'')
            cursor.execute('ALTER TABLE videos ADD COLUMN IF NOT EXISTS moderation_status TEXT DEFAULT \'safe\'')
            cursor.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT DEFAULT \'active\'')
            conn.commit()
        except: conn.rollback()

    conn.commit()
    conn.close()
    print("Military-Grade Database Initialized.")

# Run DB Init
_db_ready = True # Prevent recursion in get_db_connection during init
try:
    init_db()
except Exception as e:
    print("\n" + "!"*60)
    print("CRITICAL DATABASE CONNECTION ERROR")
    print("!"*60)
    print(f"Details: {e}")
    print("\nEXPLANATION:")
    print("You are likely trying to connect to a Render Internal Database URL")
    print("from your local computer. Internal URLs (dpg-...) ONLY work inside Render.")
    print("\nFIX:")
    print("1. Go to your Render Dashboard > PostgreSQL")
    print("2. Copy the 'EXTERNAL DATABASE URL'")
    print("3. Paste it into your local .env file.")
    print("\nFalling back to potentially unstable state...")
    print("!"*60 + "\n")
    USE_POSTGRES = False # Emergency fallback to SQLite if Postgres fails at startup
    init_db() # Try initializing SQLite instead so server can at least start

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
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
    else:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        role = 'admin' if email == ADMIN_EMAIL else 'user'
        if USE_POSTGRES:
             cursor = conn.cursor()
             cursor.execute('INSERT INTO users (email, name, picture, points, role) VALUES (%s, %s, %s, %s, %s)', 
                      (email, name, picture, 0, role))
        else:
             conn.execute('INSERT INTO users (email, name, picture, points, role) VALUES (?, ?, ?, ?, ?)', 
                      (email, name, picture, 0, role))
        conn.commit()
    else:
        # Update name/picture on login
        if USE_POSTGRES:
             cursor = conn.cursor()
             cursor.execute('UPDATE users SET name = %s, picture = %s, last_login = CURRENT_TIMESTAMP WHERE email = %s', 
                      (name, picture, email))
        else:
             conn.execute('UPDATE users SET name = ?, picture = ?, last_login = CURRENT_TIMESTAMP WHERE email = ?', 
                      (name, picture, email))
        conn.commit()
    
    # Fetch updated user
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
    else:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    user_data = to_json(user)
    user_data['is_admin'] = (user_data.get('role') == 'admin')
    
    conn.close()
    return jsonify(user_data)

@app.route('/api/add-points', methods=['POST'])
def add_points():
    data = request.json
    email = data.get('email')
    amount = data.get('amount')
    desc = data.get('description', 'Task Completion')
    
    conn = get_db_connection()
    if USE_POSTGRES:
         cursor = conn.cursor()
         cursor.execute('UPDATE users SET points = points + %s WHERE email = %s', (amount, email))
         cursor.execute('INSERT INTO transactions (user_email, amount, type, description, status) VALUES (%s, %s, %s, %s, %s)', 
                  (email, amount, 'earn', desc, 'completed'))
    else:
         conn.execute('UPDATE users SET points = points + ? WHERE email = ?', (amount, email))
         conn.execute('INSERT INTO transactions (user_email, amount, type, description, status) VALUES (?, ?, ?, ?, ?)', 
                  (email, amount, 'earn', desc, 'completed'))
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT points FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        new_points = user['points']
    else:
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
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT points FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
    else:
        user = conn.execute('SELECT points FROM users WHERE email = ?', (email,)).fetchone()
    
    if user and user['points'] >= amount_points:
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET points = points - %s WHERE email = %s', (amount_points, email))
            cursor.execute('INSERT INTO transactions (user_email, amount, type, description, status) VALUES (%s, %s, %s, %s, %s)', 
                         (email, -amount_points, 'withdraw', f'Withdrawal to {upi_id}', 'pending'))
        else:
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
        video_type = data.get('type', 'video') # 'video' or 'short'
        category = data.get('category', 'All')

        conn = get_db_connection()
        # Double check if table exists as fallback
        try:
            if USE_POSTGRES:
                check_cursor = conn.cursor()
                check_cursor.execute('SELECT 1 FROM videos LIMIT 1')
                check_cursor.close()
            else:
                conn.execute('SELECT 1 FROM videos LIMIT 1')
        except:
            print("Fallback: Table 'videos' missing in route. Re-init...")
            init_db()

        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO videos (user_email, title, description, video_url, thumbnail_url, type, category, moderation_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                         (email, title, desc, video_url, thumb_url, video_type, category, 'safe'))
        else:
            conn.execute('INSERT INTO videos (user_email, title, description, video_url, thumbnail_url, type, category, moderation_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                         (email, title, desc, video_url, thumb_url, video_type, category, 'safe'))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Upload Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def _fetch_from_cloudinary(resource_type='video'):
    """Helper: Fetch raw video resources from Cloudinary Admin API."""
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    
    if not cloud_name or not api_key or not api_secret:
        print("FAIL-SAFE ERROR: Cloudinary credentials missing in environment.")
        return []
        
    try:
        auth_str = f"{api_key}:{api_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        # Try both 'video' and 'image' (Cloudinary sometimes lists long videos as videos but small ones as raw/images in some configs)
        # But we mostly want videos
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/resources/video?max_results=500"
        headers = {'Authorization': f'Basic {encoded_auth}'}
        
        print(f"FAIL-SAFE: Calling Cloudinary Admin API for {cloud_name}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"FAIL-SAFE ERROR: Cloudinary API returned {response.status_code}: {response.text}")
            return []
            
        data = response.json()
        resources = data.get('resources', [])
        print(f"FAIL-SAFE: Found {len(resources)} assets in Cloudinary.")
        
        videos = []
        for res in resources:
            v_url = res.get('secure_url')
            p_id = res.get('public_id')
            
            # Use public_id to guess type (Shorts usually have 'short' in name if uploaded via our tool)
            v_type = 'short' if 'short' in p_id.lower() or 'snap' in p_id.lower() else 'video'
            
            videos.append({
                'id': f"cl-{res.get('asset_id', p_id)}",
                'title': p_id.split('/')[-1].replace('_', ' ').replace('-', ' ').capitalize(),
                'user_email': ADMIN_EMAIL,
                'video_url': v_url,
                'thumbnail_url': v_url.replace('.mp4', '.jpg').replace('.mov', '.jpg') if v_url else '',
                'description': f"Restored from Cloudinary Cloud ({p_id})",
                'views': 0, 'likes': 0, 'comment_count': 0,
                'timestamp': res.get('created_at'),
                'type': v_type, 'category': 'All'
            })
        return videos
    except Exception as e:
        print(f"FAIL-SAFE CRITICAL ERROR: {e}")
        return []

@app.route('/api/videos', methods=['GET'])
def get_all_videos():
    video_type = request.args.get('type')
    videos = []
    
    try:
        conn = get_db_connection()
        if video_type:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute('SELECT * FROM videos WHERE type = %s ORDER BY timestamp DESC', (video_type,))
                videos = cursor.fetchall()
            else:
                videos = conn.execute('SELECT * FROM videos WHERE type = ? ORDER BY timestamp DESC', (video_type,)).fetchall()
        else:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute('SELECT * FROM videos ORDER BY timestamp DESC')
                videos = cursor.fetchall()
            else:
                videos = conn.execute('SELECT * FROM videos ORDER BY timestamp DESC').fetchall()
        conn.close()
    except Exception as e:
        print(f"Database Query Error: {e}. Falling back to Cloudinary...")

    if not videos or len(videos) == 0:
        # FAIL-SAFE: If DB is empty or fails, fetch direct from Cloudinary
        print("FAIL-SAFE: Fetching direct from Cloudinary...")
        videos = _fetch_from_cloudinary(video_type if video_type else 'video')
        # Filter by type if Cloudinary returns more than requested
        if video_type:
            videos = [v for v in videos if v.get('type') == video_type]
        return jsonify(videos)

    return jsonify(to_json(videos))

@app.route('/api/videos/<email>', methods=['GET'])
def get_user_videos(email):
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM videos WHERE user_email = %s ORDER BY timestamp DESC', (email,))
        videos = cursor.fetchall()
    else:
        videos = conn.execute('SELECT * FROM videos WHERE user_email = ? ORDER BY timestamp DESC', (email,)).fetchall()
    conn.close()
    return jsonify(to_json(videos))


@app.route('/api/transactions/<email>', methods=['GET'])
def get_transactions(email):
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM transactions WHERE user_email = %s ORDER BY timestamp DESC LIMIT 20', (email,))
        txs = cursor.fetchall()
    else:
        txs = conn.execute('SELECT * FROM transactions WHERE user_email = ? ORDER BY timestamp DESC LIMIT 20', (email,)).fetchall()
    conn.close()
    return jsonify(to_json(txs))

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
        
        return jsonify(to_json(videos))
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
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM video_views WHERE video_id = %s AND user_email = %s', (video_id, user_email))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return jsonify({'status': 'already_viewed'})
            cursor.execute('INSERT INTO video_views (video_id, user_email) VALUES (%s, %s)', (video_id, user_email))
        else:
            existing = conn.execute('SELECT 1 FROM video_views WHERE video_id = ? AND user_email = ?', (video_id, user_email)).fetchone()
            if existing:
                conn.close()
                return jsonify({'status': 'already_viewed'})
            conn.execute('INSERT INTO video_views (video_id, user_email) VALUES (?, ?)', (video_id, user_email))

    if USE_POSTGRES:
        cursor = conn.cursor() if 'cursor' not in locals() else cursor
        cursor.execute('UPDATE videos SET views = views + 1 WHERE id = %s', (video_id,))
    else:
        conn.execute('UPDATE videos SET views = views + 1 WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/video/like', methods=['POST'])
def like_video():
    data = request.json
    video_id = data.get('video_id')
    email = data.get('email')
    
    try:
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT 1 FROM video_likes WHERE user_email = %s AND video_id = %s', (email, str(video_id)))
            already_liked = cursor.fetchone()
            
            if already_liked:
                cursor.execute('DELETE FROM video_likes WHERE user_email = %s AND video_id = %s', (email, str(video_id)))
                # Only update videos table if it's a real DB video (ID is numeric)
                if str(video_id).isdigit():
                    cursor.execute('UPDATE videos SET likes = likes - 1 WHERE id = %s', (video_id,))
                status = 'unliked'
            else:
                cursor.execute('INSERT INTO video_likes (user_email, video_id) VALUES (%s, %s)', (email, str(video_id)))
                if str(video_id).isdigit():
                    cursor.execute('UPDATE videos SET likes = likes + 1 WHERE id = %s', (video_id,))
                status = 'liked'
            conn.commit()
            
            # Get definitive like count from video_likes table
            cursor.execute('SELECT COUNT(*) as count FROM video_likes WHERE video_id = %s', (str(video_id),))
            likes = cursor.fetchone()['count']
        else:
            already_liked = conn.execute('SELECT 1 FROM video_likes WHERE user_email = ? AND video_id = ?', (email, str(video_id))).fetchone()
            
            if already_liked:
                conn.execute('DELETE FROM video_likes WHERE user_email = ? AND video_id = ?', (email, str(video_id)))
                if str(video_id).isdigit():
                    conn.execute('UPDATE videos SET likes = likes - 1 WHERE id = ?', (video_id,))
                status = 'unliked'
            else:
                conn.execute('INSERT INTO video_likes (user_email, video_id) VALUES (?, ?)', (email, str(video_id)))
                if str(video_id).isdigit():
                    conn.execute('UPDATE videos SET likes = likes + 1 WHERE id = ?', (video_id,))
                status = 'liked'
            conn.commit()
            
            likes = conn.execute('SELECT COUNT(*) FROM video_likes WHERE video_id = ?', (str(video_id),)).fetchone()[0]
                 
        conn.close()
        return jsonify({'status': status, 'likes': likes})
    except Exception as e:
        print(f"Like Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/channel/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    subscriber = data.get('subscriber')
    channel = data.get('channel')
    
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM subscriptions WHERE subscriber_email = %s AND channel_email = %s', (subscriber, channel))
        already_subbed = cursor.fetchone()
        
        if already_subbed:
            cursor.execute('DELETE FROM subscriptions WHERE subscriber_email = %s AND channel_email = %s', (subscriber, channel))
            status = 'unsubscribed'
        else:
            cursor.execute('INSERT INTO subscriptions (subscriber_email, channel_email) VALUES (%s, %s)', (subscriber, channel))
            status = 'subscribed'
        conn.commit()
        cursor.execute('SELECT COUNT(*) as count FROM subscriptions WHERE channel_email = %s', (channel,))
        count = cursor.fetchone()['count']
    else:
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
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (video_id, user_email, content) VALUES (%s, %s, %s)', (video_id, email, content))
    else:
        conn.execute('INSERT INTO comments (video_id, user_email, content) VALUES (?, ?, ?)', (video_id, email, content))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/video/comments/<video_id>', methods=['GET'])
def get_comments(video_id):
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM comments WHERE video_id = %s ORDER BY timestamp DESC', (video_id,))
        comments = cursor.fetchall()
    else:
        comments = conn.execute('SELECT * FROM comments WHERE video_id = ? ORDER BY timestamp DESC', (video_id,)).fetchall()
    conn.close()
    return jsonify(to_json(comments))

@app.route('/api/video/stats/<video_id>', methods=['POST'])
def get_video_stats(video_id):
    data = request.json or {}
    email = data.get('email', '')
    channel_email_fallback = data.get('channel_email', '') # Important for non-DB videos
    conn = get_db_connection()
    subbed = False
    
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Primary video data
        if str(video_id).isdigit():
            cursor.execute('SELECT views, likes, user_email FROM videos WHERE id = %s', (video_id,))
        else:
            cursor.execute('SELECT views, likes, user_email FROM videos WHERE id::text = %s', (str(video_id),))
        vid = cursor.fetchone()
        
        # Like status
        cursor.execute('SELECT 1 as exists FROM video_likes WHERE user_email = %s AND video_id = %s', (email, str(video_id)))
        liked = cursor.fetchone() is not None
        
        # Channel stats
        channel_email = vid['user_email'] if vid else channel_email_fallback
        if not channel_email and '@' in str(video_id): 
            channel_email = str(video_id)
            
        subs_count = 0
        if channel_email:
            cursor.execute('SELECT 1 as exists FROM subscriptions WHERE subscriber_email = %s AND channel_email = %s', (email, channel_email))
            subbed = cursor.fetchone() is not None
            cursor.execute('SELECT COUNT(*) as count FROM subscriptions WHERE channel_email = %s', (channel_email,))
            subs_count = cursor.fetchone()['count']
            
        # Global stats for this video ID
        cursor.execute('SELECT COUNT(*) as count FROM video_likes WHERE video_id = %s', (str(video_id),))
        total_likes = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM comments WHERE video_id = %s', (str(video_id),))
        comment_count = cursor.fetchone()['count']
        
        views = vid['views'] if vid else 0
        likes = total_likes if total_likes > 0 else (vid['likes'] if vid else 0)
        
    else:
        # SQLite
        vid = conn.execute('SELECT views, likes, user_email FROM videos WHERE id = ?', (video_id,)).fetchone()
        liked = conn.execute('SELECT 1 FROM video_likes WHERE user_email = ? AND video_id = ?', (email, str(video_id))).fetchone() is not None
        
        channel_email = vid['user_email'] if vid else None
        if channel_email:
            subbed = conn.execute('SELECT 1 FROM subscriptions WHERE subscriber_email = ? AND channel_email = ?', (email, channel_email)).fetchone() is not None
            subs_count = conn.execute('SELECT COUNT(*) FROM subscriptions WHERE channel_email = ?', (channel_email,)).fetchone()[0]
        else:
            subs_count = 0

        comment_count = conn.execute('SELECT COUNT(*) FROM comments WHERE video_id = ?', (str(video_id),)).fetchone()[0]
        total_likes = conn.execute('SELECT COUNT(*) FROM video_likes WHERE video_id = ?', (str(video_id),)).fetchone()[0]
        
        views = vid['views'] if vid else 0
        likes = total_likes if total_likes > 0 else (vid['likes'] if vid else 0)
        
    conn.close()
    return jsonify({
        'views': views,
        'likes': likes,
        'liked': liked,
        'subbed': subbed,
        'subscribers': subs_count,
        'comment_count': comment_count
    })

# --- Admin/Stats Routes ---

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    try:
        data = request.json
        if data.get('email') != ADMIN_EMAIL:
            return jsonify({'error': 'Unauthorized'}), 403
            
        conn = get_db_connection()
        
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            cursor.execute('SELECT SUM(points) as points FROM users')
            row = cursor.fetchone()
            total_points = row['points'] if row and row['points'] else 0
            
            cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE type='withdraw' AND status='pending'")
            pending_withdrawals = cursor.fetchone()['count']
        else:
            total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
            total_points = conn.execute('SELECT SUM(points) as points FROM users').fetchone()['points'] or 0
            pending_withdrawals = conn.execute("SELECT COUNT(*) as count FROM transactions WHERE type='withdraw' AND status='pending'").fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'total_points': total_points,
            'pending_withdrawals': pending_withdrawals,
            'db_type': 'PostgreSQL (Secure Cloud)' if USE_POSTGRES else 'SQLite (Local/Ephemeral)',
            'data_risk': not USE_POSTGRES and os.environ.get('RENDER') == 'true'
        })
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/storage/status', methods=['GET'])
def storage_status():
    return jsonify({
        'persistent': USE_POSTGRES,
        'db_type': 'PostgreSQL (Cloud Safe)' if USE_POSTGRES else 'SQLite (Ephemeral/Risk)',
        'data_risk': not USE_POSTGRES and os.environ.get('RENDER') == 'true'
    })

@app.route('/api/admin/sync-cloudinary', methods=['POST'])
def sync_cloudinary():
    """Fail-safe: Recover lost video links from Cloudinary directly."""
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    
    if not cloud_name or not api_key or not api_secret:
        return jsonify({'status': 'error', 'message': 'Cloudinary API credentials missing in .env'}), 400
        
    try:
        # Cloudinary Admin API requires Basic Auth
        auth_str = f"{api_key}:{api_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/resources/video?max_results=500"
        headers = {'Authorization': f'Basic {encoded_auth}'}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'resources' not in data:
            return jsonify({'status': 'error', 'message': 'Failed to fetch from Cloudinary', 'debug': data}), 500
            
        conn = get_db_connection()
        count = 0
        added = 0
        
        for res in data['resources']:
            video_url = res.get('secure_url')
            public_id = res.get('public_id')
            
            # Check if exists in DB
            if USE_POSTGRES:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM videos WHERE video_url = %s', (video_url,))
                exists = cursor.fetchone()
            else:
                exists = conn.execute('SELECT 1 FROM videos WHERE video_url = ?', (video_url,)).fetchone()
                
            if not exists:
                title = public_id.split('/')[-1].replace('_', ' ').capitalize()
                email = os.environ.get('ADMIN_EMAIL', 'junaidshah78634@gmail.com')
                
                if USE_POSTGRES:
                    cursor.execute('INSERT INTO videos (user_email, title, video_url, type, category) VALUES (%s, %s, %s, %s, %s)',
                                 (email, title, video_url, 'video', 'Recovered'))
                else:
                    conn.execute('INSERT INTO videos (user_email, title, video_url, type, category) VALUES (?, ?, ?, ?, ?)',
                                 (email, title, video_url, 'video', 'Recovered'))
                added += 1
            count += 1
            
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': f'Sync complete. Scanned {count} videos, restored {added} missing links.',
            'restored': added
        })
    except Exception as e:
        print(f"Sync Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/creator/stats', methods=['POST'])
def creator_stats():
    data = request.json
    email = data.get('email')
    
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT COUNT(*) as count, SUM(views) as total_views FROM videos WHERE user_email = %s', (email,))
        video_stats = cursor.fetchone()
        total_videos = video_stats['count'] if video_stats['count'] else 0
        total_views = video_stats['total_views'] if video_stats['total_views'] else 0
        cursor.execute('SELECT COUNT(*) as count FROM subscriptions WHERE channel_email = %s', (email,))
        subs_count = cursor.fetchone()['count']
    else:
        video_stats = conn.execute('SELECT COUNT(*) as count, SUM(views) as total_views FROM videos WHERE user_email = ?', (email,)).fetchone()
        total_videos = video_stats['count'] if video_stats['count'] else 0
        total_views = video_stats['total_views'] if video_stats['total_views'] else 0
        subs_count = conn.execute('SELECT COUNT(*) as count FROM subscriptions WHERE channel_email = ?', (email,)).fetchone()['count']
    
    conn.close()
    return jsonify({
        'subscribers': subs_count, 
        'views': total_views,
        'watch_time': 0,
        'video_count': total_videos
    })
@app.route('/api/admin/users', methods=['POST'])
def admin_users():
    data = request.json
    email = data.get('email')
    if email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users ORDER BY last_login DESC')
        users = cursor.fetchall()
    else:
        users = conn.execute('SELECT * FROM users ORDER BY last_login DESC').fetchall()
    
    conn.close()
    return jsonify(to_json(users))

@app.route('/api/admin/transactions', methods=['POST'])
def admin_transactions():
    data = request.json
    email = data.get('email')
    if email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM transactions ORDER BY timestamp DESC')
        txs = cursor.fetchall()
    else:
        txs = conn.execute('SELECT * FROM transactions ORDER BY timestamp DESC').fetchall()
    conn.close()
    return jsonify(to_json(txs))

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
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('UPDATE transactions SET status = %s WHERE id = %s', (new_status, tx_id))
    else:
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
            # Handle both numeric and Cloudinary string IDs
            if str(video_id).isdigit():
                cursor.execute('DELETE FROM videos WHERE id = %s', (video_id,))
            else:
                # If it's a Cloudinary ID, we can't delete from DB if not synced, 
                # but maybe it was synced with that specific string as ID (if we ever do that)
                cursor.execute('DELETE FROM videos WHERE id::text = %s', (str(video_id),))
        else:
            conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/toggle-user-status', methods=['POST'])
def toggle_user_status():
    data = request.json
    admin_email = data.get('admin_email')
    target_email = data.get('user_email')
    new_status = data.get('status') # 'active' or 'blocked'

    if admin_email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = %s WHERE email = %s', (new_status, target_email))
    else:
        conn.execute('UPDATE users SET status = ? WHERE email = ?', (new_status, target_email))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/video/delete', methods=['POST'])
def creator_delete_video():
    data = request.json
    user_email = data.get('email')
    video_id = data.get('video_id')

    conn = get_db_connection()
    
    # Verify ownership
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
                "parts": [{"text": f"Suggest a catchy video title and a 2-sentence description for a video about: {topic}. Return JSON format with 'title' and 'description' keys. Do not include markdown formatting indicators."}]
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

@app.route('/api/video/moderate', methods=['POST'])
def moderate_video():
    data = request.json
    title = data.get('title', '')
    desc = data.get('description', '')
    api_key = os.environ.get('GOOGLE_API_KEY', '').strip()
    
    if not api_key:
        return jsonify({'status': 'safe', 'message': 'Safety check skipped'})

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = f"""
        Act as a strict content moderator for Vitox Video Platform. 
        Analyze the following video details and determine if it violates our 18+ policy (nudity, sexual content, extreme violence, or hate speech).
        
        Title: {title}
        Description: {desc}
        
        Return ONLY a JSON object with two keys:
        'status': 'safe' or 'flagged'
        'reason': a short explanation if flagged, otherwise empty.
        """
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"}
            ]
        }
        
        response = requests.post(url, json=payload)
        result = response.json()
        
        # If Gemini's own safety filter blocks it, flag it immediately
        if 'promptFeedback' in result and result['promptFeedback'].get('blockReason'):
            return jsonify({'status': 'flagged', 'reason': 'Google Safety Filter Triggered'})

        text = result['candidates'][0]['content']['parts'][0]['text']
        import json, re
        clean_text = re.sub(r'```json\n?|\n?```', '', text).strip()
        mod_result = json.loads(clean_text)
        return jsonify(mod_result)
        
    except Exception as e:
        print(f"Moderation Error: {e}")
        return jsonify({'status': 'safe', 'message': 'Auto-approved (Error in Check)'})

@app.route('/api/ai/ask', methods=['POST'])
def ai_ask():
    data = request.json
    prompt = data.get('prompt', '')
    model_alias = data.get('model', 'gemini-flash')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    # Model Mapping
    models = {
        'gemini-flash': 'gemini-1.5-flash',
        'gemini-pro': 'gemini-1.5-pro',
        'llama-3-free': 'meta-llama/llama-3-8b-instruct:free',
        'mistral-free': 'mistralai/mistral-7b-instruct:free',
        'google-gemma-free': 'google/gemma-7b-it:free'
    }
    
    selected_model = models.get(model_alias, 'gemini-1.5-flash')
    
    # Handle Gemini Models
    if 'gemini' in selected_model:
        api_key = os.environ.get('GOOGLE_API_KEY', '').strip()
        if not api_key:
            return jsonify({'answer': "Gemini API key is not configured. Please use a free OpenRouter model."})
            
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            result = res.json()
            answer = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'answer': answer})
        except Exception as e:
            return jsonify({'answer': f"Gemini Error: {str(e)}"})

    # Handle OpenRouter Free Models
    else:
        api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
        if not api_key:
            return jsonify({'answer': "OpenRouter API key is not configured."})
            
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": "You are Vitox AI, a helpful assistant. Keep responses helpful and concise."},
                        {"role": "user", "content": prompt}
                    ]
                })
            )
            result = response.json()
            answer = result['choices'][0]['message']['content']
            return jsonify({'answer': answer})
        except Exception as e:
            return jsonify({'answer': f"OpenRouter Error: {str(e)}"})

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    # Keep original for compatibility if needed
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
        
    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return jsonify({'error': 'AI configuration missing'}), 500

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are Vitox AI, a helpful assistant for creators on the Vitox video platform. Keep responses concise and professional."},
                    {"role": "user", "content": prompt}
                ]
            })
        )
        result = response.json()
        answer = result['choices'][0]['message']['content']
        return jsonify({'answer': answer})
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        return jsonify({'answer': "I'm having trouble connecting to my brain right now. Please try again later!"})

@app.route('/api/admin/backup', methods=['POST'])
def admin_backup():
    try:
        data = request.json
        req_email = data.get('email')
        
        if not req_email or req_email != ADMIN_EMAIL:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        conn = get_db_connection()
        backup_data = {}
        
        # Tables to backup - using a try-except block for each ensures partial backups if a table is missing
        tables = ['users', 'videos', 'transactions', 'subscriptions', 'video_likes', 'comments']
        
        # Helper to convert row to dict
        def row_to_dict(row):
            d = dict(row)
            # Pre-process datetimes to strings
            for k, v in d.items():
                if isinstance(v, (datetime, date)):
                    d[k] = v.isoformat()
            return d

        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Ensure RealDictCursor is used
            for table in tables:
                try:
                    cursor.execute(f'SELECT * FROM {table}')
                    rows = cursor.fetchall()
                    backup_data[table] = [row_to_dict(row) for row in rows]
                except Exception as e:
                    print(f"Backup skip table {table}: {e}")
                    conn.rollback() # Important for Postgres transaction errors
                    continue
        else:
            for table in tables:
                try:
                    rows = conn.execute(f'SELECT * FROM {table}').fetchall()
                    backup_data[table] = [row_to_dict(row) for row in rows]
                except Exception as e:
                    print(f"Backup skip table {table}: {e}")
                    continue

        conn.close()
        
        # Return as downloadable file
        import json
        json_str = json.dumps(backup_data, indent=2)
        
        from flask import make_response
        response = make_response(json_str)
        response.headers['Content-Type'] = 'application/json'
        filename = f'vitox_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    except Exception as e:
        print(f"Backup Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/style.css')
def serve_css():
    from flask import make_response
    with open(os.path.join(BASE_DIR, 'style.css'), 'r', encoding='utf-8') as f:
        content = f.read()
    response = make_response(content)
    response.headers['Content-Type'] = 'text/css'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

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


@app.route('/api/collab/chat/send', methods=['POST'])
def send_collab_message():
    try:
        data = request.json
        sender_email = data.get('sender_email')
        receiver_email = data.get('receiver_email')
        content = data.get('content')
        
        if not sender_email or not receiver_email or not content:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor()
            # Get sender info (points and brand status)
            cursor.execute('SELECT points, is_verified_brand FROM users WHERE email = %s', (sender_email,))
            sender = cursor.fetchone()
            sender_points = sender[0] if sender else 0
            
            # Get receiver subscriber count
            cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE channel_email = %s', (receiver_email,))
            squad_count = cursor.fetchone()[0]
            
            # 1M Squad requirement for Elite Creators (> 100k subs)
            if squad_count > 100000 and (sender_points or 0) < 1000000:
                conn.close()
                return jsonify({'status': 'error', 'message': '1M Square/Points required to chat with Elite Creators (100k+ Squad)'}), 403

            cursor.execute('INSERT INTO messages (sender_email, receiver_email, content) VALUES (%s, %s, %s)',
                         (sender_email, receiver_email, content))
        else:
            sender = conn.execute('SELECT points, is_verified_brand FROM users WHERE email = ?', (sender_email,)).fetchone()
            sender_points = sender['points'] if sender else 0
            
            squad_count = conn.execute('SELECT COUNT(*) FROM subscriptions WHERE channel_email = ?', (receiver_email,)).fetchone()[0]
            # Enforce 1M Points rule for creators with > 1k subs on SQLite (test mode)
            if squad_count > 1000 and (sender_points or 0) < 1000000:
                conn.close()
                return jsonify({'status': 'error', 'message': '1M Square/Points required'}), 403

            conn.execute('INSERT INTO messages (sender_email, receiver_email, content) VALUES (?, ?, ?)',
                         (sender_email, receiver_email, content))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/brand/apply', methods=['POST'])
def apply_brand_verification():
    try:
        data = request.json
        email = data.get('email')
        conn = get_db_connection()
        # For now, we just mark them as 'pending_brand' in a new status or use role
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = 'pending_brand' WHERE email = %s", (email,))
        else:
            conn.execute("UPDATE users SET status = 'pending_brand' WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Application submitted! Admin will verify your brand.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/collab/chat/history', methods=['GET'])
def get_chat_history():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT * FROM messages 
            WHERE (sender_email = %s AND receiver_email = %s)
            OR (sender_email = %s AND receiver_email = %s)
            ORDER BY timestamp ASC
        ''', (user1, user2, user2, user1))
        rows = cursor.fetchall()
    else:
        rows = conn.execute('''
            SELECT * FROM messages 
            WHERE (sender_email = ? AND receiver_email = ?)
            OR (sender_email = ? AND receiver_email = ?)
            ORDER BY timestamp ASC
        ''', (user1, user2, user2, user1)).fetchall()
        
    messages = [dict(r) for r in rows]
    conn.close()
    return jsonify(messages)

# --- ADMINISTRATIVE PANEL APIS ---
@app.route('/api/admin/stats')
@admin_required
def get_platform_stats():
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        u_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM videos")
        v_count = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(views) FROM videos")
        total_views = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(points) FROM users")
        total_points = cursor.fetchone()[0] or 0
    else:
        u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        v_count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        total_views = conn.execute("SELECT SUM(views) FROM videos").fetchone()[0] or 0
        total_points = conn.execute("SELECT SUM(points) FROM users").fetchone()[0] or 0
    conn.close()
    return jsonify({
        'users': u_count,
        'videos': v_count,
        'views': total_views,
        'points': total_points
    })

@app.route('/api/admin/users')
@admin_required
def get_all_users():
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users ORDER BY last_login DESC")
        rows = cursor.fetchall()
    else:
        rows = conn.execute("SELECT * FROM users ORDER BY last_login DESC").fetchall()
    users = [dict(r) for r in rows]
    conn.close()
    return jsonify(users)

@app.route('/api/admin/user/action', methods=['POST'])
@admin_required
def admin_user_action():
    data = request.json
    target_email = data.get('email')
    action = data.get('action') # 'verify_brand', 'ban', 'unban', 'make_admin'
    
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor()
        if action == 'verify_brand':
            cursor.execute("UPDATE users SET is_verified_brand = TRUE, status = 'active' WHERE email = %s", (target_email,))
        elif action == 'ban':
            cursor.execute("UPDATE users SET status = 'banned' WHERE email = %s", (target_email,))
        elif action == 'unban':
            cursor.execute("UPDATE users SET status = 'active' WHERE email = %s", (target_email,))
    else:
        if action == 'verify_brand':
            conn.execute("UPDATE users SET is_verified_brand = 1, status = 'active' WHERE email = ?", (target_email,))
        elif action == 'ban':
            conn.execute("UPDATE users SET status = 'banned' WHERE email = ?", (target_email,))
        elif action == 'unban':
            conn.execute("UPDATE users SET status = 'active' WHERE email = ?", (target_email,))
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': f'Action {action} applied to {target_email}'})

@app.route('/api/admin/video/delete', methods=['DELETE'])
@admin_required
def admin_delete_video():
    video_id = request.args.get('id')
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
    else:
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/admin/chat/send', methods=['POST'])
@admin_required
def api_admin_chat_send():
    data = request.json
    receiver_email = data.get('receiver_email')
    content = data.get('content')
    admin_email = request.headers.get('X-Admin-Email')

    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (sender_email, receiver_email, content, is_admin, is_collab) VALUES (%s, %s, %s, %s, %s)',
                     (admin_email, receiver_email, content, True, False))
    else:
        conn.execute('INSERT INTO messages (sender_email, receiver_email, content, is_admin, is_collab) VALUES (?, ?, ?, ?, ?)',
                     (admin_email, receiver_email, content, 1, 0))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/admin/chat/history', methods=['GET'])
def get_admin_chat_history():
    user_email = request.args.get('email')
    admin_email = os.environ.get('ADMIN_EMAIL', 'junaidshah78634@gmail.com')
    
    conn = get_db_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT * FROM messages 
            WHERE (sender_email = %s AND receiver_email = %s)
            OR (sender_email = %s AND receiver_email = %s)
            ORDER BY timestamp ASC
        ''', (admin_email, user_email, user_email, admin_email))
        rows = cursor.fetchall()
    else:
        rows = conn.execute('''
            SELECT * FROM messages 
            WHERE (sender_email = ? AND receiver_email = ?)
            OR (sender_email = ? AND receiver_email = ?)
            ORDER BY timestamp ASC
        ''', (admin_email, user_email, user_email, admin_email)).fetchall()
        
    messages = [dict(r) for r in rows]
    conn.close()
    return jsonify(messages)

# --- COMMUNITY POSTS APIS ---
@app.route('/api/posts/create', methods=['POST'])
def create_post():
    try:
        data = request.json
        user_email = data.get('user_email')
        content = data.get('content')
        image_url = data.get('image_url', '')

        if not user_email or not content:
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400

        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posts (user_email, content, image_url) VALUES (%s, %s, %s)',
                         (user_email, content, image_url))
        else:
            conn.execute('INSERT INTO posts (user_email, content, image_url) VALUES (?, ?, ?)',
                         (user_email, content, image_url))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/posts', methods=['GET'])
def get_posts():
    user_email = request.args.get('email')
    conn = get_db_connection()
    if user_email:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('SELECT * FROM posts WHERE user_email = %s ORDER BY timestamp DESC', (user_email,))
            rows = cursor.fetchall()
        else:
            rows = conn.execute('SELECT * FROM posts WHERE user_email = ? ORDER BY timestamp DESC', (user_email,)).fetchall()
    else:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('SELECT * FROM posts ORDER BY timestamp DESC')
            rows = cursor.fetchall()
        else:
            rows = conn.execute('SELECT * FROM posts ORDER BY timestamp DESC').fetchall()
    
    posts = [dict(r) for r in rows]
    conn.close()
    return jsonify(posts)

# Deploy ID: 1739556815

# Initial DB Setup on Start
try:
    init_db()
except Exception as e:
    print(f"Startup DB Init Failed (Non-Fatal): {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
