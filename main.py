import sqlite3
import requests
import os
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# --- BEAST FIREBASE (SQLite Logic) ---
DB_PATH = 'beast_studio.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users table: name, plan (free/paid), ai_credits, joined_date
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  plan TEXT DEFAULT 'FREE', 
                  credits INTEGER DEFAULT 10)''')
    
    # Designs table: user_id, filename, timestamp
    c.execute('''CREATE TABLE IF NOT EXISTS designs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  filename TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Create storage folder
if not os.path.exists('designs'):
    os.makedirs('designs')

# AI Generation Route
@app.route('/api/generate-logo', methods=['POST'])
def generate_logo():
    data = request.json
    prompt = data.get('prompt')
    api_key = data.get('apiKey')
    provider = data.get('provider', 'openrouter') # openrouter, openai, gemini
    model = data.get('model', 'google/gemini-2.0-flash-exp:free')

    if not api_key:
        return jsonify({"status": "error", "message": "API Key is required"}), 400

    try:
        if provider == 'openrouter':
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": f"Create a professional minimalist logo description for: {prompt}. Give me colors and layout."}]
                }
            )
            return jsonify(response.json())
        
        elif provider == 'gemini':
            # Simplified Gemini implementation
            return jsonify({"status": "success", "message": "Gemini integration active"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('.', 'login.html')

@app.route('/studio')
def studio():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Beast Backend is running on port {port}")
    app.run(host='0.0.0.0', port=port)
