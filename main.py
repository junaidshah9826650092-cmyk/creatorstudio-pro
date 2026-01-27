import sqlite3
import requests
import os
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# --- BEAST FIREBASE (SQLite Logic) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beast_studio.db')
DESIGNS_PATH = os.path.join(BASE_DIR, 'designs')
BEAST_SERVER_API_KEY = os.environ.get("BEAST_API_KEY", "sk-or-v1-xxxxxxxx") # Security: Use Env Var

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Security: Explicit CSP for AdSense and Google Auth
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://pagead2.googlesyndication.com https://unpkg.com https://*.google.com https://*.googlesyndication.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://*; frame-src https://accounts.google.com https://googleads.g.doubleclick.net https://*.google.com;"
    return response

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT UNIQUE, 
                      email TEXT,
                      password TEXT, 
                      plan TEXT DEFAULT 'FREE', 
                      credits INTEGER DEFAULT 999999,
                      last_login DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS designs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT, 
                      filename TEXT, 
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        # ADVANCED: Projects Table for "Edit Later" functionality
        c.execute('''CREATE TABLE IF NOT EXISTS projects 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT, 
                      name TEXT,
                      json_data TEXT,
                      thumbnail_url TEXT,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at: {DB_PATH}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")

# Initialization
init_db()
if not os.path.exists(DESIGNS_PATH):
    os.makedirs(DESIGNS_PATH)
if not os.path.exists(os.path.join(BASE_DIR, 'project_thumbs')):
    os.makedirs(os.path.join(BASE_DIR, 'project_thumbs'))

# --- AI ADVANCED ENDPOINTS ---

@app.route('/api/ai/magic-text', methods=['POST'])
def ai_magic_text():
    """Generates viral titles or slogans based on a topic"""
    data = request.json
    topic = data.get('topic')
    mode = data.get('mode', 'thumbnail') # 'thumbnail' or 'logo'
    
    if not topic:
        return jsonify({"status": "error", "message": "Topic required"}), 400

    prompt = f"Give me 5 viral, clickbait youtube thumbnail titles about: {topic}" if mode == 'thumbnail' else f"Give me 5 modern, minimalist slogan ideas for a brand named: {topic}"

    try:
        # Mock response for speed/demo (since credits are unlimited)
        return jsonify({
            "status": "success",
            "ideas": [
                f"The SECRET to {topic} Revealed 🤫",
                f"Stop Doing {topic} Wrong! 🛑",
                f"I Tried {topic} for 24 Hours via AI",
                f"{topic} Masterclass: 0 to Hero",
                f"Why {topic} Changes EVERYTHING"
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- PROJECT MANAGEMENT (CANVA-LIKE FEATURES) ---

@app.route('/api/projects/save', methods=['POST'])
def save_project():
    """Saves the editable state of the project"""
    data = request.json
    username = data.get('username')
    name = data.get('name', 'Untitled Project')
    json_state = data.get('json_data') # The fabric.js/canvas JSON
    thumb_data = data.get('thumbnail') # Base64 preview
    
    if not username or not json_state:
        return jsonify({"status": "error", "message": "Invalid data"}), 400
        
    try:
        # Save Thumbnail
        thumb_url = ""
        if thumb_data:
            header, encoded = thumb_data.split(",", 1)
            decoded = base64.b64decode(encoded)
            fname = f"project_thumbs/{username}_{os.urandom(4).hex()}.png"
            with open(os.path.join(BASE_DIR, fname), "wb") as f:
                f.write(decoded)
            thumb_url = fname

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if project exists (update) or new (insert)
        c.execute("INSERT INTO projects (username, name, json_data, thumbnail_url) VALUES (?, ?, ?, ?)",
                  (username, name, str(json_data), thumb_url))
        conn.commit()
        project_id = c.lastrowid
        conn.close()
        
        return jsonify({"status": "success", "message": "Project saved successfully!", "id": project_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/projects/list', methods=['GET'])
def list_projects():
    username = request.args.get('username')
    if not username:
        return jsonify({"status": "error", "message": "Login required"}), 401
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, thumbnail_url, updated_at FROM projects WHERE username=? ORDER BY updated_at DESC", (username,))
    projects = [{"id": r[0], "name": r[1], "thumbnail": r[2], "date": r[3]} for r in c.fetchall()]
    conn.close()
    
    return jsonify({"status": "success", "projects": projects})

# --- EXISTING ENDPOINTS (KEPT & ENHANCED) ---

@app.route('/api/generate-logo', methods=['POST'])
def generate_logo():
    data = request.json
    username = data.get('username')
    prompt = data.get('prompt')
    user_api_key = data.get('apiKey')
    provider = data.get('provider', 'openrouter')
    model = data.get('model', 'google/gemini-2.0-flash-exp:free')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT plan, credits FROM users WHERE username=?", (username,))
    user = c.fetchone()
    
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    plan, credits = user[0], user[1]
    
    final_api_key = user_api_key
    
    # UNLIMITED ACCESS MODE
    if not final_api_key or "xxxx" in final_api_key:
        final_api_key = BEAST_SERVER_API_KEY
        
    if not final_api_key or "xxxx" in final_api_key:
         return jsonify({"status": "error", "message": "Server API Key not configured. Please add key for unlimited mode."}), 500

    # BYPASS CREDIT CHECK
    # if credits < credit_cost: ...

    try:
        # ENHANCED PROMPT ENGINEERING
        system_prompt = "You are a professional graphic designer. Respond ONLY with a description of a visual design."
        full_prompt = f"{system_prompt} Create a detailed visual description for: {prompt}. Specify hex colors, geometric shapes, and layout for a high-converting {provider} design."
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {final_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://beaststudio.com", 
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": full_prompt}]
            }
        )
        
        if response.status_code == 200:
            # NO CREDIT DEDUCTION - UNLIMITED
            res_data = response.json()
            res_data['remaining_credits'] = 999999 
            return jsonify(res_data)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/user-status', methods=['POST'])
def get_user_status():
    data = request.json
    username = data.get('username')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT plan, credits FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"status": "success", "plan": user[0], "credits": user[1]})
    return jsonify({"status": "error", "message": "User not found"}), 404

@app.route('/api/buy-plan', methods=['POST'])
def buy_plan():
    data = request.json
    username = data.get('username')
    plan_type = data.get('plan') # 'PRO' or 'BEAST'
    
    credits_to_add = 300 if plan_type == 'PRO' else 1000
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET plan=?, credits=credits+? WHERE username=?", (plan_type, credits_to_add, username))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Successfully upgraded to {plan_type}! {credits_to_add} credits added."})

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/login')
def login_page():
    return send_from_directory(BASE_DIR, 'login.html')

@app.route('/studio')
def studio():
    return send_from_directory(BASE_DIR, 'studio.html')

@app.route('/privacy')
def privacy():
    return send_from_directory(BASE_DIR, 'privacy-policy.html')

@app.route('/terms')
def terms():
    return send_from_directory(BASE_DIR, 'terms.html')

@app.route('/admin')
def admin_panel():
    return send_from_directory(BASE_DIR, 'admin.html')

# FINAL SYNC VERSION 2.1
@app.route('/ads.txt')
def ads_txt():
    return "google.com, pub-6894674624448360, DIRECT, f08c47fec0942fa0"

@app.route('/test-ads')
def test_ads():
    return "TEST: pub-6894674624448360"

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(BASE_DIR, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(BASE_DIR, 'sitemap.xml')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(BASE_DIR, path)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')  # This will be the email
    password = data.get('password', '1234')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Simple Firebase-style user check/creation
    c.execute("SELECT plan, credits, email FROM users WHERE username=?", (username,))
    user = c.fetchone()
    
    if not user:
        # Create as Free user if not exists - store email
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, username, password))
        conn.commit()
        plan, credits = 'FREE', 10
    else:
        plan, credits = user[0], user[1]
        # Update last login time and ensure email is set
        c.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP, email=? WHERE username=?", (username, username))
        conn.commit()
    
    conn.close()
    return jsonify({
        "status": "success", 
        "user": username, 
        "plan": plan, 
        "credits": credits,
        "message": f"Welcome {username}! Plan: {plan}"
    })

@app.route('/api/save-design', methods=['POST'])
def save_design():
    data = request.json
    img_data = data.get('image')
    username = data.get('username', 'Guest')
    name = data.get('name', 'beast_design')
    
    if img_data:
        header, encoded = img_data.split(",", 1)
        decoded = base64.b64decode(encoded)
        filename = f"designs/{username}_{os.urandom(4).hex()}.png"
        
        with open(filename, "wb") as f:
            f.write(decoded)
            
        # Log to "Firebase" DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO designs (username, filename) VALUES (?, ?)", (username, filename))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "file": filename})
    
    return jsonify({"status": "error", "message": "No image data"}), 400

# Admin Routes
@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Total users
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        # Premium users
        c.execute("SELECT COUNT(*) FROM users WHERE plan='PRO' OR plan='BEAST'")
        premium_users = c.fetchone()[0]
        
        # Total designs
        c.execute("SELECT COUNT(*) FROM designs")
        total_designs = c.fetchone()[0]
        
        # Revenue estimate (PRO users * 500 + BEAST users * 1500)
        c.execute("SELECT COUNT(*) FROM users WHERE plan='PRO'")
        pro_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE plan='BEAST'")
        beast_count = c.fetchone()[0]
        revenue = (pro_count * 500) + (beast_count * 1500)
        
        # All users with email and last login
        c.execute("SELECT username, email, plan, credits, last_login FROM users ORDER BY last_login DESC")
        users = [{
            "username": row[0], 
            "email": row[1] or row[0],  # Fallback to username if no email
            "plan": row[2], 
            "credits": row[3],
            "lastLogin": row[4]
        } for row in c.fetchall()]
        
        conn.close()
        
        return jsonify({
            "totalUsers": total_users,
            "premiumUsers": premium_users,
            "totalDesigns": total_designs,
            "revenue": revenue,
            "users": users
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/update-credits', methods=['POST'])
def update_credits():
    data = request.json
    username = data.get('username')
    credits = data.get('credits', 0)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET credits=? WHERE username=?", (credits, username))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Running on 0.0.0.0 to allow mobile access on same WiFi
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Beast Backend is running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
