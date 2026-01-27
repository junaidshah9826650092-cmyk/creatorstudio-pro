// ==========================================
// Beast Studio - Authorization System
// Mobile & Desktop Scroll System with Admin Panel
// ==========================================

// Admin Configuration
const ADMIN_EMAIL = 'junaidshah78634@gmail.com';

// ==========================================
// Triple-Click Logo for Admin Panel
// ==========================================

let logoClickCount = 0;
let logoClickTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    // Triple-click logo for admin access
    const logo = document.querySelector('.logo');

    if (logo) {
        logo.addEventListener('click', () => {
            logoClickCount++;

            // Reset counter after 1 second
            clearTimeout(logoClickTimer);
            logoClickTimer = setTimeout(() => {
                logoClickCount = 0;
            }, 1000);

            // Triple-click detected
            if (logoClickCount === 3) {
                logoClickCount = 0;
                clearTimeout(logoClickTimer);
                checkAdminAccess();
            }
        });

        //Add cursor pointer to indicate clickable
        logo.style.cursor = 'pointer';
        logo.title = 'Triple-click for admin access';
    }
});

// Check if current user is admin and open panel
function checkAdminAccess() {
    const currentEmail = localStorage.getItem('beast_email');

    if (currentEmail === ADMIN_EMAIL) {
        showNotification('🛡️ Admin Access Granted - Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = 'admin.html';
        }, 800);
    } else {
        // Easter egg for non-admin users
        showNotification('🔒 Secret discovered! Admin access restricted to ' + ADMIN_EMAIL, 'info');
        // Visual feedback
        const logo = document.querySelector('.logo');
        if (logo) {
            logo.style.animation = 'shake 0.5s';
        }
    }
}

// Add shake animation
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
`;
document.head.appendChild(shakeStyle);

// ==========================================
// Scroll Animations Observer
// ==========================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Observe all scroll animation elements
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll(
        '.scroll-fade-in, .scroll-slide-in, .scroll-slide-up, .scroll-zoom-in'
    );

    animatedElements.forEach(el => {
        scrollObserver.observe(el);
    });
});

// ==========================================
// Navigation Scroll Effect
// ==========================================

let lastScroll = 0;
const nav = document.getElementById('main-nav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 50) {
        nav.classList.add('scrolled');
    } else {
        nav.classList.remove('scrolled');
    }

    lastScroll = currentScroll;
});

// ==========================================
// Form Switching
// ==========================================

function switchToSignup() {
    const loginCard = document.getElementById('login-card');
    const signupCard = document.getElementById('signup-card');

    loginCard.style.animation = 'slideOutLeft 0.3s ease-out';

    setTimeout(() => {
        loginCard.classList.add('hidden');
        signupCard.classList.remove('hidden');
        signupCard.style.animation = 'slideInRight 0.3s ease-out';
    }, 300);
}

function switchToLogin() {
    const loginCard = document.getElementById('login-card');
    const signupCard = document.getElementById('signup-card');

    signupCard.style.animation = 'slideOutRight 0.3s ease-out';

    setTimeout(() => {
        signupCard.classList.add('hidden');
        loginCard.classList.remove('hidden');
        loginCard.style.animation = 'slideInLeft 0.3s ease-out';
    }, 300);
}

// Add slide animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutLeft {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(-100px); opacity: 0; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100px); opacity: 0; }
    }
    @keyframes slideInLeft {
        from { transform: translateX(-100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideInRight {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

// ==========================================
// Password Toggle
// ==========================================

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;

    if (input.type === 'password') {
        input.type = 'text';
        button.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
        `;
    } else {
        input.type = 'password';
        button.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
            </svg>
        `;
    }
}

// ==========================================
// Password Strength Checker
// ==========================================

const signupPassword = document.getElementById('signup-password');
if (signupPassword) {
    signupPassword.addEventListener('input', (e) => {
        const password = e.target.value;
        const strengthIndicator = document.querySelector('.strength-bar');
        const strengthText = document.querySelector('.strength-text');

        let strength = 0;

        // Length check
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;

        // Character variety checks
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^a-zA-Z0-9]/.test(password)) strength++;

        // Update UI
        strengthIndicator.className = 'strength-bar';

        if (strength <= 2) {
            strengthIndicator.classList.add('weak');
            strengthText.textContent = 'Weak';
            strengthText.style.color = '#ef4444';
        } else if (strength <= 4) {
            strengthIndicator.classList.add('medium');
            strengthText.textContent = 'Medium';
            strengthText.style.color = '#f59e0b';
        } else {
            strengthIndicator.classList.add('strong');
            strengthText.textContent = 'Strong';
            strengthText.style.color = '#10b981';
        }
    });
}

// ==========================================
// Form Validation & Submission
// ==========================================

const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const rememberMe = document.getElementById('remember-me').checked;

        // Show loading state
        const submitBtn = loginForm.querySelector('.btn-primary');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                <line x1="12" y1="2" x2="12" y2="6"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                <line x1="2" y1="12" x2="6" y2="12"/>
                <line x1="18" y1="12" x2="22" y2="12"/>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
            </svg>
            <span>Signing In...</span>
        `;
        submitBtn.disabled = true;

        try {
            // Call backend with email/password
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: email, password })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Store user data INCLUDING email
                localStorage.setItem('beast_user', data.user);
                localStorage.setItem('beast_email', email); // Store email for admin check
                localStorage.setItem('beast_plan', data.plan);
                localStorage.setItem('beast_credits', data.credits);

                // Show special message for admin
                if (email === ADMIN_EMAIL) {
                    showNotification('🛡️ Welcome Admin! Triple-click logo anytime for admin panel.', 'success');
                } else {
                    showNotification('Welcome back! Redirecting...', 'success');
                }

                // Redirect to studio
                setTimeout(() => {
                    window.location.href = 'studio.html';
                }, 1500);
            } else {
                throw new Error(data.message || 'Login failed');
            }

        } catch (error) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            showNotification(error.message || 'Login failed. Please try again.', 'error');
        }
    });
}

if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const agreeTerms = document.getElementById('agree-terms').checked;

        if (!agreeTerms) {
            showNotification('Please accept the Terms and Privacy Policy', 'error');
            return;
        }

        // Validate password strength
        const strengthBar = document.querySelector('.strength-bar');
        if (!strengthBar.classList.contains('strong') && !strengthBar.classList.contains('medium')) {
            showNotification('Please use a stronger password', 'error');
            return;
        }

        const submitBtn = signupForm.querySelector('.btn-primary');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                <line x1="12" y1="2" x2="12" y2="6"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                <line x1="2" y1="12" x2="6" y2="12"/>
                <line x1="18" y1="12" x2="22" y2="12"/>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
            </svg>
            <span>Creating Account...</span>
        `;
        submitBtn.disabled = true;

        try {
            // Call backend
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: email, password })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Store user data INCLUDING email
                localStorage.setItem('beast_user', data.user);
                localStorage.setItem('beast_email', email); // Store email for admin check
                localStorage.setItem('beast_plan', data.plan);
                localStorage.setItem('beast_credits', data.credits);

                // Show success message
                showNotification('Account created! Redirecting...', 'success');

                // Redirect to studio
                setTimeout(() => {
                    window.location.href = 'studio.html';
                }, 1500);
            } else {
                throw new Error(data.message || 'Signup failed');
            }

        } catch (error) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            showNotification(error.message || 'Signup failed. Please try again.', 'error');
        }
    });
}

// ==========================================
// Social Login Functions
// ==========================================

async function loginWithGoogle() {
    showNotification('Google authentication coming soon!', 'info');
    // TODO: Implement Google OAuth
    // This would integrate with your backend's Google OAuth endpoint
}

async function loginWithGithub() {
    showNotification('GitHub authentication coming soon!', 'info');
    // TODO: Implement GitHub OAuth
    // This would integrate with your backend's GitHub OAuth endpoint
}

// ==========================================
// Notification System
// ==========================================

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.beast-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `beast-notification ${type}`;

    const icons = {
        success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>`,
        error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>`,
        info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>`
    };

    notification.innerHTML = `
        ${icons[type] || icons.info}
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Add notification styles
const notificationStyle = document.createElement('style');
notificationStyle.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .beast-notification {
        position: fixed;
        top: 100px;
        right: 20px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        color: white;
        font-weight: 500;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transform: translateX(400px);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 10000;
        max-width: 400px;
    }
    
    .beast-notification.show {
        transform: translateX(0);
    }
    
    .beast-notification.success {
        border-color: rgba(16, 185, 129, 0.5);
        background: rgba(16, 185, 129, 0.1);
    }
    
    .beast-notification.error {
        border-color: rgba(239, 68, 68, 0.5);
        background: rgba(239, 68, 68, 0.1);
    }
    
    .beast-notification.info {
        border-color: rgba(99, 102, 241, 0.5);
        background: rgba(99, 102, 241, 0.1);
    }
    
    .beast-notification svg {
        min-width: 20px;
    }
    
    @media (max-width: 768px) {
        .beast-notification {
            right: 10px;
            left: 10px;
            max-width: none;
        }
    }
`;
document.head.appendChild(notificationStyle);

// ==========================================
// Smooth Scroll for Navigation Links
// ==========================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && document.querySelector(href)) {
            e.preventDefault();
            document.querySelector(href).scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ==========================================
// Auto-detect User's Previous Session
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const savedUser = localStorage.getItem('beast_user');
    const savedEmail = localStorage.getItem('beast_email');
    const currentPage = window.location.pathname;

    // If user is logged in and on auth page, show notification
    if (savedUser && currentPage.includes('auth.html')) {
        if (savedEmail === ADMIN_EMAIL) {
            showNotification(`🛡️ Welcome back Admin! Triple-click logo for admin panel.`, 'info');
        } else {
            showNotification(`Welcome back, ${savedUser}! Redirecting to studio...`, 'info');
        }
        setTimeout(() => {
            window.location.href = 'studio.html';
        }, 2000);
    }
});

// ==========================================
// Parallax Scroll Effect for Background Orbs
// ==========================================

window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const orbs = document.querySelectorAll('.gradient-orb');

    orbs.forEach((orb, index) => {
        const speed = 0.5 + (index * 0.1);
        orb.style.transform = `translateY(${scrolled * speed}px)`;
    });
});

// ==========================================
// Form Input Animation
// ==========================================

const inputs = document.querySelectorAll('.input-wrapper input');
inputs.forEach(input => {
    input.addEventListener('focus', (e) => {
        e.target.parentElement.style.transform = 'scale(1.01)';
        e.target.parentElement.style.transition = 'transform 0.2s ease';
    });

    input.addEventListener('blur', (e) => {
        e.target.parentElement.style.transform = 'scale(1)';
    });
});

// ==========================================
// Keyboard Navigation Enhancement
// ==========================================

document.addEventListener('keydown', (e) => {
    // Escape key closes modals (future enhancement)
    if (e.key === 'Escape') {
        // Close any open modals
    }

    // Tab navigation enhancement
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-nav');
    }
});

document.addEventListener('mousedown', () => {
    document.body.classList.remove('keyboard-nav');
});

console.log('🚀 Beast Studio Authorization System Loaded');
console.log('📱 Mobile & Desktop Responsive');
console.log('🎨 Smooth Scroll Animations Active');
console.log('🛡️ Admin Panel: Triple-click logo (Admin: ' + ADMIN_EMAIL + ')');
