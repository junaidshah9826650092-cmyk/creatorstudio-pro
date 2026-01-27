# 🚀 Beast Studio - Mobile & Desktop Authorization System

## ✨ Features Implemented

### 1. **Modern Authorization Page** (`auth.html`)
- ✅ Responsive design for mobile and desktop
- ✅ Smooth scroll animations
- ✅ Glassmorphism UI design
- ✅ Login and signup forms
- ✅ Password strength indicator
- ✅ Social login placeholders (Google & GitHub)
- ✅ Features & pricing sections
- ✅ Premium aesthetics with gradient animations

### 2. **Admin Panel Access** 🛡️
- ✅ **Triple-click the Beast Studio logo** to access admin panel
- ✅ **Admin Email:** `junaidshah78634@gmail.com`
- ✅ Only admin can access admin panel
- ✅ Non-admin users see a secret discovery message

### 3. **Gmail Login Tracking**
- ✅ All logged-in Gmail accounts are stored in database
- ✅ Email addresses visible in admin panel
- ✅ Last login timestamp tracked
- ✅ Admin email highlighted with 🛡️ badge

### 4. **Admin Dashboard** (`admin.html`)
Shows:
- Total users count
- Premium users (PRO + BEAST plans)
- Total designs created
- Estimated revenue
- **Complete user table with:**
  - Gmail/Email address
  - Username
  - Plan type (FREE/PRO/BEAST)
  - Credit balance
  - Last login time
  - Edit credits button

### 5. **Database Schema**
Updated SQLite database with:
```sql
users:
  - id (PRIMARY KEY)
  - username (UNIQUE)
  - email (Gmail address)
  - password
  - plan (FREE/PRO/BEAST)
  - credits (INTEGER)
  - last_login (DATETIME)
```

## 🎯 How to Use

### For Regular Users:
1. Visit `auth.html`
2. Sign up or login with your email
3. Get redirected to Beast Studio

### For Admin (junaidshah78634@gmail.com):
1. Login with admin email
2. **Triple-click the Beast Studio logo** (top left)
3. Admin panel opens automatically
4. View all registered users, their Gmail accounts, and last login times
5. Manage user credits
6. Track revenue and statistics

## 🔐 Admin Access

The admin system works as follows:

1. **Triple-Click Logo Detection:**
   - Click the Beast Studio logo 3 times within 1 second
   - System checks if logged-in email == `junaidshah78634@gmail.com`
   - If admin: Redirects to admin panel
   - If not admin: Shows "secret discovered" message

2. **Admin Protection:**
   - `/admin.html` checks localStorage for `beast_email`
   - Only allows `junaidshah78634@gmail.com`
   - Others are redirected to homepage

## 📱 Mobile & Desktop Responsive

All pages work flawlessly on:
- ✅ Mobile phones (320px+)
- ✅ Tablets (768px+)
- ✅ Desktops (1024px+)
- ✅ Large screens (1440px+)

## 🎨 Design Features

1. **Smooth Scroll Animations:**
   - Fade in 
   - Slide in from sides
   - Slide up
   - Zoom in
   - Parallax background orbs

2. **Interactive Elements:**
   - Hover effects
   - Click animations
   - Loading spinners
   - Toast notifications
   - Password strength meter

3. **Premium Aesthetics:**
   - Glassmorphism cards
   - Gradient backgrounds
   - Animated orbs
   - Star field
   - Smooth transitions

## 🚀 Running the Application

```bash
# Start the Flask backend
python main.py

# Visit in browser
http://localhost:5000/auth.html
```

## 📊 Admin Panel View

When admin logs in and triple-clicks logo:

```
Admin Dashboard
🛡️ junaidshah78634@gmail.com

Stats Cards:
┌─────────────┬────────────────┬──────────────┬──────────────┐
│ Total Users │ Premium Users  │ Total Designs│   Revenue    │
│      10     │       3        │     45       │   ₹2500      │
└─────────────┴────────────────┴──────────────┴──────────────┘

User Table:
┌────────────────────────────────┬──────────┬──────┬────────┬───────────────┬─────────┐
│ Email / Gmail                  │ Username │ Plan │Credits │ Last Login    │ Actions │
├────────────────────────────────┼──────────┼──────┼────────┼───────────────┼─────────┤
│🛡️ junaidshah78634@gmail.com   │ admin    │ BEAST│  1000  │ 2026-01-27... │ [Edit]  │
│ user1@gmail.com                │ user1    │ PRO  │   300  │ 2026-01-26... │ [Edit]  │
│ user2@gmail.com                │ user2    │ FREE │    10  │ 2026-01-25... │ [Edit]  │
└────────────────────────────────┴──────────┴──────┴────────┴───────────────┴─────────┘
```

## 🎯 Key Files Modified/Created

1. **`auth.html`** - Beautiful authorization page
2. **`auth.css`** - Responsive styling with animations
3. **`auth.js`** - Form logic, admin access, scroll animations
4. **`main.py`** - Backend with email tracking
5. **`admin.html`** - Enhanced admin dashboard

## 💡 Pro Tips

- Admin can edit any user's credits
- Password strength must be Medium or Strong for signup
- All emails are automatically tracked
- Last login updates on every login
- Mobile users can also triple-tap logo for admin access

---

**Made with ❤️ for Beast Studio**
**Admin Email: junaidshah78634@gmail.com**
