import sqlite3
import requests
import os
import base64
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# --- BEAST FIREBASE (SQLite Logic) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beast_studio.db')
DESIGNS_PATH = os.path.join(BASE_DIR, 'designs')
BEAST_SERVER_API_KEY = os.environ.get("BEAST_API_KEY", "sk-or-v1-xxxxxxxx") # Security: Use Env Var

# Initialize Gemini
genai.configure(api_key=BEAST_SERVER_API_KEY)
# We handle both OpenRouter (legacy) and Gemini (new tools) locally
gemini_model = genai.GenerativeModel('gemini-pro')

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
                      credits INTEGER DEFAULT 100,
                      last_login DATETIME DEFAULT CURRENT_TIMESTAMP,
                      last_reset DATE DEFAULT CURRENT_DATE)''')
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
        # NEW: Creator Hub Resources Table
        c.execute('''CREATE TABLE IF NOT EXISTS resources 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, 
                      type TEXT, 
                      category TEXT, 
                      file_url TEXT, 
                      thumb_url TEXT,
                      is_trending BOOLEAN DEFAULT 0,
                      is_premium BOOLEAN DEFAULT 0,
                      downloads INTEGER DEFAULT 0,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        # NEW: Use Case Packs Table
        c.execute('''CREATE TABLE IF NOT EXISTS packs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      name TEXT, 
                      description TEXT, 
                      thumb_url TEXT,
                      resource_ids TEXT, 
                      is_premium BOOLEAN DEFAULT 0)''')
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at: {DB_PATH}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")

# Initialization
init_db()
if not os.path.exists(DESIGNS_PATH):
    os.makedirs(DESIGNS_PATH)

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

# --- RESOURCE HUB ENDPOINTS ---
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

@app.route('/api/user-status', methods=['GET', 'POST'])
def get_user_status():
    if request.method == 'POST':
        data = request.json or {}
        username = data.get('username')
    else:
        username = request.args.get('username')

    if not username:
        return jsonify({"status": "error", "message": "Username required"}), 400

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

@app.route('/privacy')
def privacy():
    return send_from_directory(BASE_DIR, 'privacy-policy.html')

@app.route('/terms')
def terms():
    return send_from_directory(BASE_DIR, 'terms.html')

@app.route('/admin')
def admin_panel():
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/library')
def library():
    return send_from_directory(BASE_DIR, 'library.html')

@app.route('/ai-tools')
def ai_tools():
    return send_from_directory(BASE_DIR, 'ai-tools.html')

@app.route('/meme-maker')
def meme_maker():
    return send_from_directory(BASE_DIR, 'meme-maker.html')

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
    
    # Daily Credit Reset Logic
    c.execute("SELECT credits, last_reset FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row:
        curr_credits, last_reset = row[0], row[1]
        from datetime import date
        today = str(date.today())
        
        if last_reset != today:
            # Top up to 100 if they are below (Free users)
            new_credits = max(curr_credits, 100)
            c.execute("UPDATE users SET credits=?, last_reset=? WHERE username=?", (new_credits, today, username))
            conn.commit()
            credits = new_credits

    conn.close()
    return jsonify({
        "status": "success", 
        "user": username, 
        "plan": plan, 
        "credits": credits,
        "message": f"Welcome back! Daily credits refilled." if row and row[1] != str(date.today()) else f"Welcome {username}!"
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

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/api/ai/creator-studio', methods=['POST'])
def creator_studio_api():
    """Gemini-powered Creator Studio with Credit Management"""
    data = request.json
    username = data.get('username')
    tool_type = data.get('tool_type') # 'title', 'script', 'hook', 'thumbnail', 'hashtag'
    topic = data.get('topic')
    
    if not username or not tool_type or not topic:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # 1. Credit Check Logic
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        
        # Default to 100 if user doesn't exist (simulated for guest)
        credits = user_row[0] if user_row else 100
        cost = 5 

        if credits < cost:
            conn.close()
            return jsonify({"status": "error", "message": "Insufficient credits! Refill to continue."}), 403

        # 2. Tool Prompt Engineering (POWERED BY BEAST AI)
        prompts = {
            "title": f"You are a viral YouTube expert. Topic: {topic}. Give me 10 HIGH CTR, CLICKBAIT titles that focus on curiosity or fear of missing out. Return ONLY a JSON list of strings.",
            "script": f"Write a 60-second viral Short/Reel script for: {topic}. Structure: [0-5s] Aggressive Hook, [5-50s] Fast-paced Value/Story, [50-60s] Viral Loop/CTA. Return ONLY JSON with keys 'hook', 'body', 'onscreen_text' (list).",
            "hook": f"Generate 5 scroll-stopping hooks for a Reel about: {topic}. Use the 'Negativity Bias' or 'Open Loop' strategies. Return ONLY as a JSON list.",
            "hashtag": f"Generate 15 trending hashtags for: {topic}. Include high-reach and niche hashtags. Return ONLY as a JSON list.",
            "viral_pack": f"Generate a FULL viral content pack for: {topic}. Include: 5 Titles, 3 Hooks, 1 Script, 3 Thumbnail Text ideas. Return ONLY JSON.",
            "style_analyzer": f"Analyze this YouTube video concept: '{topic}'. Give a 1-10 Viral Potential Score and 3 tips to increase CTR. Return ONLY JSON."
        }

        # Premium Cost Adjustment
        if tool_type == "viral_pack": cost = 15
        elif tool_type == "style_analyzer": cost = 8

        prompt = prompts.get(tool_type)
        if not prompt:
            conn.close()
            return jsonify({"status": "error", "message": "Invalid tool"}), 400

        # Call Gemini
        response = gemini_model.generate_content(prompt)
        text = response.text
        # Safety cleaning for JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Remove any leading/trailing garbage
        text = text.strip()
        if not text.startswith('[') and not text.startswith('{'):
             # Attempt to find the first bracket/brace
             start_idx = min(text.find('['), text.find('{')) if '[' in text and '{' in text else (text.find('[') if '[' in text else text.find('{'))
             end_idx = max(text.rfind(']'), text.rfind('}')) if ']' in text and '}' in text else (text.rfind(']') if ']' in text else text.rfind('}'))
             if start_idx != -1 and end_idx != -1:
                 text = text[start_idx:end_idx+1]

        result_data = json.loads(text)

        # 3. Deduct Credits
        if user_row:
            cursor.execute("UPDATE users SET credits = credits - ? WHERE username = ?", (cost, username))
            conn.commit()

        conn.close()
        return jsonify({
            "status": "success", 
            "result": result_data,
            "remaining_credits": credits - cost
        })

    except Exception as e:
        print(f"DEBUG AI: {str(e)}")
        return jsonify({"status": "error", "message": "AI Generation Failed. Please try later."}), 500

# --- RESOURCE HUB ENDPOINTS ---

@app.route('/api/resources', methods=['GET'])
def get_resources():
    rtype = request.args.get('type') # meme, sound, overlay
    category = request.args.get('category')
    trending = request.args.get('trending')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = "SELECT * FROM resources WHERE 1=1"
    params = []
    
    if rtype:
        query += " AND type = ?"
        params.append(rtype)
    if category:
        query += " AND category = ?"
        params.append(category)
    if trending:
        query += " AND is_trending = 1"
        
    query += " ORDER BY downloads DESC"
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    resources = []
    for r in rows:
        resources.append({
            "id": r[0], "title": r[1], "type": r[2], "category": r[3],
            "file_url": r[4], "thumb_url": r[5], "trending": r[6],
            "premium": r[7], "downloads": r[8]
        })
    return jsonify({"status": "success", "resources": resources})

@app.route('/api/packs', methods=['GET'])
def get_packs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM packs")
    rows = c.fetchall()
    conn.close()
    
    packs = []
    for r in rows:
        packs.append({
            "id": r[0], "name": r[1], "description": r[2],
            "thumb_url": r[3], "resource_ids": r[4], "premium": r[5]
        })
    return jsonify({"status": "success", "packs": packs})

@app.route('/api/resource/download', methods=['POST'])
def track_download():
    data = request.json
    rid = data.get('id')
    if not rid: return jsonify({"status": "error"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE resources SET downloads = downloads + 1 WHERE id = ?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/survey/submit', methods=['POST'])
def submit_survey():
    """Submit feedback and get 50 credits reward"""
    data = request.json
    username = data.get('username')
    feedback = data.get('feedback') # Could be a dict or string
    
    if not username:
        return jsonify({"status": "error", "message": "Login required"}), 401
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. Update credits
        bonus = 50
        c.execute("UPDATE users SET credits = credits + ? WHERE username = ?", (bonus, username))
        
        # 2. Log feedback (Simple table for now)
        c.execute("CREATE TABLE IF NOT EXISTS surveys (id INTEGER PRIMARY KEY, username TEXT, data TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("INSERT INTO surveys (username, data) VALUES (?, ?)", (username, str(feedback)))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "50 Credits added to your account! Thanks for helping us grow.", "new_credits_bonus": bonus})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Running on 0.0.0.0 to allow mobile access on same WiFi
    port = int(os.environ.get("PORT", 5000))
    
    # Auto-detect Local IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print("\n" + "="*50)
    print(f"🚀 BEAST STUDIO IS ONLINE!")
    print(f"💻 PC Access:     http://localhost:{port}")
    print(f"📱 Mobile Access: http://{local_ip}:{port}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
