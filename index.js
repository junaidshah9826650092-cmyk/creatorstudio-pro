// Beast Core Initialization
lucide.createIcons();

const canvas = document.getElementById('beast-canvas');
const ctx = canvas.getContext('2d');

// Beast Presets
const presets = {
    'yt-thumb': { w: 1280, h: 720 },
    'logo': { w: 800, h: 800 },
    'insta': { w: 1080, h: 1080 },
    'ios': { w: 1024, h: 1024 }
};

// Final Strict Auth Guard
const savedUser = localStorage.getItem('beast_user');

if (!savedUser && !window.location.pathname.includes('/login')) {
    window.location.href = '/login';
}

document.addEventListener('DOMContentLoaded', () => {
    if (savedUser) {
        updateUserUI(savedUser, localStorage.getItem('beast_plan') || 'FREE');
    }
});

let currentType = 'yt-thumb';
let uploadedImg = null;

// Controls
const textInput = document.getElementById('editor-text');
const sizeSlider = document.getElementById('size-slider');
const textColor = document.getElementById('text-color');
const bgColor = document.getElementById('bg-color');
const gradType = document.getElementById('gradient-type');
const exportBtn = document.getElementById('export-btn');
const uploadInput = document.getElementById('upload-input');
const presetChips = document.querySelectorAll('.preset-chip');

function initBeast() {
    const config = presets[currentType];
    canvas.width = config.w;
    canvas.height = config.h;

    // Smooth Scale
    const container = document.querySelector('.viewport');
    const zoom = Math.min((container.clientWidth - 160) / config.w, (container.clientHeight - 160) / config.h);

    canvas.style.width = (config.w * zoom) + 'px';
    canvas.style.height = (config.h * zoom) + 'px';

    render();
}

function render() {
    const w = canvas.width;
    const h = canvas.height;

    // 1. Background System
    ctx.clearRect(0, 0, w, h);

    if (gradType.value === 'none') {
        ctx.fillStyle = bgColor.value;
        ctx.fillRect(0, 0, w, h);
    } else if (gradType.value === 'linear') {
        let g = ctx.createLinearGradient(0, 0, w, h);
        g.addColorStop(0, bgColor.value);
        g.addColorStop(1, '#000000');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, w, h);
    } else if (gradType.value === 'mesh') {
        // Simple faux mesh
        ctx.fillStyle = bgColor.value;
        ctx.fillRect(0, 0, w, h);
        let g2 = ctx.createRadialGradient(w, 0, 0, w, 0, w);
        g2.addColorStop(0, 'rgba(255,255,255,0.2)');
        g2.addColorStop(1, 'transparent');
        ctx.fillStyle = g2;
        ctx.fillRect(0, 0, w, h);
    }

    // 2. Image Layer
    if (uploadedImg) {
        const scale = Math.min(w / uploadedImg.width, h / uploadedImg.height) * 0.9;
        const dw = uploadedImg.width * scale;
        const dh = uploadedImg.height * scale;
        ctx.drawImage(uploadedImg, (w - dw) / 2, (h - dh) / 2, dw, dh);
    }

    // 3. Text System (Beast Typography)
    const text = textInput.value;
    const size = parseInt(sizeSlider.value);

    ctx.font = `800 ${size}px 'Outfit'`;
    ctx.fillStyle = textColor.value;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Pro Shadow
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 20;
    ctx.shadowOffsetX = 10;
    ctx.shadowOffsetY = 10;

    ctx.fillText(text, w / 2, h / 2);

    // Clean shadow for next ops
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
}

// Interactivity
[textInput, sizeSlider, textColor, bgColor, gradType].forEach(el => {
    el.addEventListener('input', render);
});

presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
        presetChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentType = chip.dataset.type;
        initBeast();
    });
});

uploadInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            const img = new Image();
            img.onload = () => {
                uploadedImg = img;
                render();
            };
            img.src = ev.target.result;
        };
        reader.readAsDataURL(file);
    }
});

// Removed local download listener (consolidated into saveToBeastServer)

function resetBeast() {
    uploadedImg = null;
    textInput.value = "BEAST MODE";
    sizeSlider.value = 100;
    render();
}

// AI & Backend Handlers
function toggleModelList() {
    const provider = document.getElementById('ai-provider').value;
    const modelList = document.getElementById('ai-model');
    modelList.innerHTML = '';

    if (provider === 'openrouter') {
        modelList.innerHTML = `
            <option value="google/gemini-2.0-flash-exp:free">Gemini 2.0 Free</option>
            <option value="mistralai/mistral-7b-instruct:free">Mistral 7B Free</option>
            <option value="meta-llama/llama-3.1-8b-instruct:free">Llama 3.1 Free</option>
            <option value="openai/gpt-4o">GPT-4o (Pro)</option>
        `;
    } else if (provider === 'gemini') {
        modelList.innerHTML = `<option value="gemini-pro">Gemini Pro</option>`;
    } else {
        modelList.innerHTML = `<option value="gpt-3.5-turbo">GPT-3.5 Turbo</option><option value="gpt-4">GPT-4</option>`;
    }
}

window.openAIModal = () => {
    document.getElementById('ai-modal').style.display = 'flex';
    lucide.createIcons();
};
window.closeAIModal = () => {
    document.getElementById('ai-modal').style.display = 'none';
};

async function generateWithAI() {
    const provider = document.getElementById('ai-provider').value;
    const apiKey = document.getElementById('ai-api-key').value;
    const model = document.getElementById('ai-model').value;
    const prompt = document.getElementById('ai-prompt').value; // Updated to read from modal textarea

    if (!apiKey) return alert("Please enter your API Key!");
    if (!prompt) return alert("Please tell BEAST what to create!");

    const aiText = document.getElementById('ai-btn-text');
    if (aiText) aiText.innerText = 'INITIALIZING BEAST AI...';

    try {
        const response = await fetch('/api/generate-logo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, apiKey, provider, model })
        });
        const data = await response.json();

        if (data.choices && data.choices[0].message) {
            const resultText = data.choices[0].message.content;
            textInput.value = resultText.substring(0, 30);
            render();
            alert("AI Design Idea Received!");
            closeAIModal(); // Auto-close on success
        } else {
            alert("AI Response Error. Check your API key.");
        }
    } catch (e) {
        alert("AI Offline. Please check your connection.");
    } finally {
        if (aiText) aiText.innerText = 'INITIALIZE GENERATION';
    }
}

function openBeastLogin() {
    document.getElementById('login-modal').style.display = 'flex';
}

async function beastBackendLogin() {
    const username = document.getElementById('beast-user').value;
    if (!username) return alert("Please enter a name!");

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('login-modal').style.display = 'none';
            localStorage.setItem('beast_user', data.user);
            localStorage.setItem('beast_plan', data.plan);
            localStorage.setItem('beast_credits', data.credits);

            updateUserUI(data.user, data.plan);
            alert(data.message);
        }
    } catch (e) {
        document.getElementById('login-modal').style.display = 'none';
        alert("Beast Studio: Offline Mode Enabled");
    }
}

function updateUserUI(user, plan) {
    const btn = document.getElementById('main-login-btn');
    const display = document.getElementById('user-display');
    const color = plan === 'PRO' ? '#fbbf24' : '#6366f1';

    if (display) {
        display.innerHTML = `<span style="color:${color};">●</span> ${user}`;
    }

    if (btn) {
        btn.innerHTML = `<i data-lucide="shield-check" size="18" style="vertical-align:middle;"></i> ${plan} MODE`;
    }
    lucide.createIcons();
}

async function saveToBeastServer() {
    const imgData = canvas.toDataURL('image/png');
    const name = textInput.value || "beast_design";
    const username = localStorage.getItem('beast_user') || "Guest";

    // 1. Mandatory Local Download
    const link = document.createElement('a');
    link.download = `${name}-${Date.now()}.png`;
    link.href = imgData;
    link.click();

    // 2. Optional Server Save
    try {
        const response = await fetch('/api/save-design', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imgData, name, username })
        });
        const data = await response.json();
        if (data.status === 'success') {
            console.log("Design saved to server:", data.file);
        }
    } catch (e) {
        console.warn("Backend offline. Design preserved locally.");
    }
}

window.onGoogleSignIn = (resp) => {
    // Decoding JWT from Google (Simple version for display)
    try {
        const payload = JSON.parse(atob(resp.credential.split('.')[1]));
        console.log("Beast Authenticated:", payload.name);

        localStorage.setItem('beast_user', payload.name);
        localStorage.setItem('beast_plan', 'FREE');
        updateUserUI(payload.name, 'FREE');

        alert(`Welcome, ${payload.name}! You are now in the Studio.`);
    } catch (e) {
        console.error("Google Auth Error:", e);
    }
};

window.openBeastLogin = openBeastLogin;
window.beastBackendLogin = beastBackendLogin;
window.resetBeast = resetBeast;

// Update Export button to use backend if available
exportBtn.onclick = saveToBeastServer;

// Start
window.addEventListener('resize', initBeast);
initBeast();
