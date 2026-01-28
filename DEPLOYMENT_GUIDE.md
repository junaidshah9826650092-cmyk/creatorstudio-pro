# 🚀 Beast Studio - Pro Deployment Cheat Sheet

Follow this workflow to keep your site 24/7 Live, Mobile-Safe (HTTPS), and Professional.

---

## 🛠️ Step 1: The Daily Workflow (Git Push)

Every time you finish a feature (like adding a new tool or fixing a bug), run these 3 commands in your terminal:

1. **Stage your work:**
   `git add .`

2. **Commit your changes:**
   `git commit -m "Brief description of what you did"`

3. **Push to the Cloud:**
   `git push origin main`

---

## 🌐 Step 2: Hosting the Frontend (Vercel / Netlify)
*Best for: `index.html`, `studio.html`, `index.js`, `index.css`*

1. Go to [Vercel.com](https://vercel.com) or [Netlify.com](https://netlify.com).
2. Login with your **GitHub** account.
3. Click **"Add New Project"**.
4. Import your repository: `creatorstudio-pro`.
5. **Deployment:** Click "Deploy".
6. **Result:** You get a `https://beast-studio.vercel.app` URL instantly.
   - ✅ **SSL (HTTPS)** is automatic.
   - ✅ **Mobile-Safe** connection.
   - ✅ **24/7 Live** (even if your PC is off).

---

## ⚙️ Step 3: Hosting the Backend (Render.com)
*Best for: `main.py`, `beast_studio.db`, `requirements.txt`*

Since you have a Python/Flask backend, use **Render**:

1. Login to [Render.com](https://render.com) with **GitHub**.
2. Click **"New"** -> **"Web Service"**.
3. Connect your repo.
4. **Settings:**
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`
5. **Environment Variables:**
   - Add your `GEMINI_API_KEY` here.
6. **Result:** You get a backend URL like `https://beast-api.onrender.com`.

---

## 🔗 Step 4: Connecting Frontend to Backend

In your `index.js` or wherever you make API calls, update the URL:

```javascript
// OLD (Local):
fetch('http://127.0.0.1:5000/api/ai/creator-studio')

// NEW (Live):
fetch('https://your-backend-url.onrender.com/api/ai/creator-studio')
```

---

## 🏆 Founder Pro-Tips:
1. **Auto-Deploy:** Every time you `git push`, Vercel and Render will automatically update your site. Zero manual work.
2. **Custom Domain:** Buy a `.com` or `.in` and connect it to Vercel settings for a 100% professional look.
3. **Health Check:** Always test the mobile URL immediately after pushing.
