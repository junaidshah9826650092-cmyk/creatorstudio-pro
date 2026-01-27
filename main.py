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
                      password TEXT, 
                      plan TEXT DEFAULT 'FREE', 
                      credits INTEGER DEFAULT 10)''')
        c.execute('''CREATE TABLE IF NOT EXISTS designs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT, 
                      filename TEXT, 
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at: {DB_PATH}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")

# Initialization
init_db()
if not os.path.exists(DESIGNS_PATH):
    os.makedirs(DESIGNS_PATH)

# AI Generation Route
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
    
    # Logic: If PRO/BEAST, use server key, otherwise use user key
    final_api_key = user_api_key
    credit_cost = 5 # Default cost
    
    if plan in ['PRO', 'BEAST']:
        final_api_key = BEAST_SERVER_API_KEY
        credit_cost = 10 if plan == 'PRO' else 2 # BEAST plan gets cheaper credits
        
    if not final_api_key or "xxxx" in final_api_key:
        if plan == 'FREE':
            return jsonify({"status": "error", "message": "FREE users must provide their own API Key"}), 400
        else:
            return jsonify({"status": "error", "message": "Internal AI Server Error. Contact Admin."}), 500

    if credits < credit_cost:
        return jsonify({"status": "error", "message": f"Low Credits! You need {credit_cost} credits, you have {credits}."}), 403

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {final_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": f"Create a professional minimalist logo description for: {prompt}. Give me colors and layout."}]
            }
        )
        
        # Deduct credits if successful
        if response.status_code == 200:
            new_credits = credits - credit_cost
            c.execute("UPDATE users SET credits=? WHERE username=?", (new_credits, username))
            conn.commit()
            res_data = response.json()
            res_data['remaining_credits'] = new_credits
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
    username = data.get('username')
    password = data.get('password', '1234')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Simple Firebase-style user check/creation
    c.execute("SELECT plan, credits FROM users WHERE username=?", (username,))
    user = c.fetchone()
    
    if not user:
        # Create as Free user if not exists
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        plan, credits = 'FREE', 10
    else:
        plan, credits = user[0], user[1]
    
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
        c.execute("SELECT COUNT(*) FROM users WHERE plan='PRO'")
        premium_users = c.fetchone()[0]
        
        # Total designs
        c.execute("SELECT COUNT(*) FROM designs")
        total_designs = c.fetchone()[0]
        
        # Revenue estimate (PRO users * 500)
        revenue = premium_users * 500
        
        # All users
        c.execute("SELECT username, plan, credits FROM users ORDER BY id DESC")
        users = [{"username": row[0], "plan": row[1], "credits": row[2]} for row in c.fetchall()]
        
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
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Beast Backend is running on port {port}")
    app.run(host='0.0.0.0', port=port)
