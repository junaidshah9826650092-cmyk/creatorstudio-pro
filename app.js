// Google Sign-In Config
const CLIENT_ID = "792653327676-kn08t8c5vduqbmva15nngmrcfvuv2l60.apps.googleusercontent.com";
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
    google.accounts.id.prompt();
}

function updateUI() {
    if (user) {
        pointsDisplay.textContent = user.points.toLocaleString();
        const rupees = user.points * conversionRate;
        rupeeDisplay.textContent = `₹${rupees.toFixed(2)}`;
        userNameDisplay.textContent = user.name;
        loginBtn.textContent = 'Sign Out';
        loginBtn.onclick = signOut;
    } else {
        pointsDisplay.textContent = '0';
        rupeeDisplay.textContent = '₹0.00';
        userNameDisplay.textContent = 'Guest User';
        loginBtn.textContent = 'Sign In';
        loginBtn.onclick = loginWithGoogle;
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
};
