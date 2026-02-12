// Google Sign-In Config
const CLIENT_ID = "109192770054200088033.apps.googleusercontent.com";
const API_URL = "/api";

// App State
let user = JSON.parse(localStorage.getItem('swift_user')) || null;
const conversionRate = 10 / 500; // 10 Rupees for 500 points

// UI Elements
const pointsDisplay = document.getElementById('total-points');
const rupeeDisplay = document.getElementById('rupee-amount');
const adOverlay = document.getElementById('ad-overlay');
const adCountdown = document.getElementById('ad-countdown');
const userNameDisplay = document.getElementById('user-name');
const loginBtn = document.getElementById('login-btn');
const historyList = document.getElementById('history-list');

// Initialize Google Auth
function initGoogleAuth() {
    if (typeof google === 'undefined') return;
    google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: onGoogleSignIn
    });
}

async function onGoogleSignIn(resp) {
    try {
        const base64Url = resp.credential.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(window.atob(base64));

        // Sync with Backend
        const response = await fetch(`${API_URL}/user`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: payload.email,
                name: payload.name
            })
        });

        const dbUser = await response.json();
        user = dbUser;
        localStorage.setItem('swift_user', JSON.stringify(user));

        updateUI();
        showToast(`Welcome, ${user.name}!`);
    } catch (e) {
        console.error(e);
        showToast('Login Failed', 'error');
    }
}

function loginWithGoogle() {
    if (user) {
        signOut();
    } else {
        google.accounts.id.prompt();
    }
}

function updateUI() {
    if (user) {
        pointsDisplay.textContent = user.points.toLocaleString();
        const rupees = user.points * conversionRate;
        rupeeDisplay.textContent = `₹${rupees.toFixed(2)}`;
        userNameDisplay.textContent = user.name;
        document.getElementById('user-avatar').textContent = user.name.charAt(0).toUpperCase();
        loginBtn.textContent = 'Sign Out';

        // Admin Access
        const adminBtn = document.getElementById('admin-btn');
        if (user.is_admin) {
            adminBtn.style.display = 'block';
        } else {
            adminBtn.style.display = 'none';
        }

        fetchHistory();
    } else {
        userNameDisplay.textContent = 'Guest User';
        document.getElementById('user-avatar').textContent = '?';
        loginBtn.textContent = 'Sign In';
        document.getElementById('admin-btn').style.display = 'none';
        historyList.innerHTML = '<div style="background: var(--bg-card); padding: 20px; border-radius: 20px; text-align: center; color: var(--text-dim); font-size: 0.9rem;">Sign in to see history</div>';
    }
    lucide.createIcons();
}

async function fetchHistory() {
    if (!user) return;
    try {
        const res = await fetch(`${API_URL}/transactions/${user.email}`);
        const txs = await res.json();

        if (txs.length === 0) {
            historyList.innerHTML = '<div style="background: var(--bg-card); padding: 20px; border-radius: 20px; text-align: center; color: var(--text-dim); font-size: 0.9rem;">No transactions yet.</div>';
            return;
        }

        historyList.innerHTML = txs.map(tx => `
            <div style="background: var(--bg-card); border: 1px solid var(--glass-border); padding: 15px 20px; border-radius: 20px; display: flex; justify-content: space-between; align-items: center;">
                <div style="text-align: left;">
                    <div style="font-weight: 600; font-size: 0.95rem;">${tx.description}</div>
                    <div style="font-size: 0.75rem; color: var(--text-dim);">${new Date(tx.timestamp).toLocaleDateString()}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 700; color: ${tx.amount > 0 ? 'var(--primary)' : '#ff4d4d'};">
                        ${tx.amount > 0 ? '+' : ''}${tx.amount} Pts
                    </div>
                    <div style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">${tx.status}</div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

function signOut() {
    localStorage.removeItem('swift_user');
    user = null;
    updateUI();
    showToast('Signed Out');
}

// Task Actions
async function addPoints(amount, description) {
    if (!user) {
        showToast('Please Sign In first!', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/add-points`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: user.email,
                amount: amount,
                description: description
            })
        });

        const data = await response.json();
        user.points = data.new_points;
        localStorage.setItem('swift_user', JSON.stringify(user));
        updateUI();
        showToast(`${amount} Points Added!`);
    } catch (e) {
        showToast('Error saving points');
    }
}

function startAdTask(name, reward) {
    if (!user) { return showToast('Sign In first!'); }

    adOverlay.style.display = 'flex';
    let timeLeft = 15;
    adCountdown.textContent = timeLeft;

    const timer = setInterval(() => {
        timeLeft--;
        adCountdown.textContent = timeLeft;
        if (timeLeft <= 0) {
            clearInterval(timer);
            adOverlay.style.display = 'none';
            addPoints(reward, `Watched: ${name}`);
        }
    }, 1000);
}

function simulateTask(name, reward) {
    addPoints(reward, name);
}

// Simple Toast Notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'success' ? 'var(--primary)' : '#ef4444'};
        color: ${type === 'success' ? 'black' : 'white'};
        padding: 12px 24px;
        border-radius: 100px;
        font-weight: 700;
        z-index: 3000;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        animation: fadeInUp 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// Withdraw simulation
async function openWithdraw() {
    if (!user) return showToast('Sign In first!');

    const rupees = user.points * conversionRate;
    if (rupees < 50) {
        alert("Minimum withdrawal is ₹50.");
    } else {
        const upi = prompt("Enter UPI ID:");
        if (upi) {
            const resp = await fetch(`${API_URL}/withdraw`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: user.email,
                    points: user.points,
                    upi_id: upi
                })
            });
            const data = await resp.json();
            if (data.status === 'success') {
                showToast('Withdrawal Requested!');
                user.points = 0;
                localStorage.setItem('swift_user', JSON.stringify(user));
                updateUI();
            }
        }
    }
}

window.onload = () => {
    initGoogleAuth();
    updateUI();

    // Professional Preloader Removal
    setTimeout(() => {
        const preloader = document.getElementById('preloader');
        if (preloader) {
            preloader.style.transition = 'opacity 0.5s ease, visibility 0.5s';
            preloader.style.opacity = '0';
            preloader.style.visibility = 'hidden';
            setTimeout(() => preloader.remove(), 500);
        }
    }, 1500);
};
