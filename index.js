/**
 * BEAST STUDIO - PRO DESIGN ENGINE v1.0
 * Core: Object-Based State, Selection Engine, Transform Controls
 */

let canvas, ctx;
let layers = [];
let selectedId = null;
let isDragging = false;
let isResizing = false;
let activeHandle = null; // 'nw', 'ne', 'sw', 'se'
let dragStartX, dragStartY;
let lastX, lastY;
let showGrid = false;
let gridSpacing = 40;

const MASTER_TEMPLATES = {
    'gaming_reaction': {
        name: 'Epic Reaction',
        layers: [
            { type: 'shape', shapeType: 'rect', x: 640, y: 360, width: 1280, height: 720, color: '#111827', opacity: 1, locked: true },
            { type: 'shape', shapeType: 'triangle', x: 200, y: 200, width: 300, height: 300, color: '#ef4444', opacity: 0.8 },
            { type: 'text', text: 'EPIC REACTION!', x: 640, y: 150, fontSize: 100, fontWeight: '900', color: '#fbbf24', fontFamily: 'Outfit' },
            { type: 'text', text: 'You Won\'t Believe This...', x: 640, y: 550, fontSize: 50, fontWeight: '600', color: '#ffffff', fontFamily: 'Outfit' }
        ]
    },
    'clean_vlog': {
        name: 'Clean Minimal',
        layers: [
            { type: 'shape', shapeType: 'rect', x: 640, y: 360, width: 1280, height: 720, color: '#f8fafc', opacity: 1, locked: true },
            { type: 'shape', shapeType: 'circle', x: 1000, y: 200, width: 400, height: 400, color: '#6366f1', opacity: 0.2 },
            { type: 'text', text: 'MY MORNING ROUTINE', x: 400, y: 360, fontSize: 70, fontWeight: '900', color: '#1e293b', fontFamily: 'Outfit' },
            { type: 'text', text: 'Episode 04', x: 400, y: 440, fontSize: 30, fontWeight: '500', color: '#64748b', fontFamily: 'Outfit' }
        ]
    }
};

// History for Undo/Redo
let history = [];
let historyIndex = -1;

const SNAP_THRESHOLD = 8;
const HANDLE_SIZE = 8;

// --- INITIALIZATION ---

function initBeast() {
    canvas = document.getElementById('beast-canvas');
    if (!canvas) {
        console.warn("Editor canvas not found. Skipping initialization.");
        return;
    }
    ctx = canvas.getContext('2d');

    // Set default size (16:9)
    resizeCanvas(1280, 720);

    // Event Listeners (Canvas and Global)
    canvas.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('resize', debouncedResize);

    // Initial Lucide check
    requestAnimationFrame(() => {
        if (window.lucide) lucide.createIcons();
    });

    // Load existing layers or default
    const saved = localStorage.getItem('beast_last_design');
    if (saved) {
        try {
            layers = JSON.parse(saved);
            // Re-hydrate images
            layers.forEach(l => {
                if (l.type === 'image') {
                    l.img = new Image();
                    l.img.src = l.src;
                }
            });
        } catch (e) { layers = []; }
    }

    if (layers.length === 0) {
        addTextLayer("BEAST STUDIO", canvas.width / 2, canvas.height / 2);
    }

    saveState();
    syncUserStatus();
    render();
    console.log("🚀 Beast Engine Ready");
}

let resizeTimeout;
function debouncedResize() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (canvas) resizeCanvas(canvas.width, canvas.height);
    }, 200);
}

function switchTab(tabId, el) {
    // Hide all panels
    document.querySelectorAll('.panel-content').forEach(p => p.style.display = 'none');
    // Deactivate all nav items
    document.querySelectorAll('.nav-item').forEach(n => {
        n.classList.remove('active');
        n.style.color = '#94a3b8';
    });

    // Show selected
    const target = document.getElementById('tab-' + tabId);
    if (target) target.style.display = 'block';
    el.classList.add('active');
    el.style.color = tabId === 'magic' ? '#fbbf24' : '#fff';

    if (window.lucide) lucide.createIcons();
}

function updateCursor(e) {
    if (isDragging || isResizing) return;
    const { x, y } = getMousePos(e);

    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        if (layer && !layer.locked) {
            const handle = getHandleAt(x, y, layer);
            if (handle) {
                canvas.style.cursor = (handle === 'nw' || handle === 'se') ? 'nwse-resize' : 'nesw-resize';
                return;
            }
        }
    }

    const hit = [...layers].reverse().find(l => !l.hidden && isPointInLayer(x, y, l));
    canvas.style.cursor = hit ? 'move' : 'default';
}

function loadBeastTemplate(key) {
    const template = MASTER_TEMPLATES[key];
    if (template) {
        layers = JSON.parse(JSON.stringify(template.layers));
        saveState();
        render();
        showToast(`Template Loaded: ${template.name}`);
    }
}

function resizeCanvas(w, h) {
    canvas.width = w;
    canvas.height = h;
    const wrapper = canvas.parentElement;
    if (!wrapper || wrapper.clientWidth < 100) {
        canvas.style.transform = `scale(0.5)`; // Fallback
        render();
        return;
    }
    const scale = Math.min((wrapper.clientWidth - 40) / w, (wrapper.clientHeight - 40) / h);
    canvas.style.transform = `scale(${scale})`;
    render();
}

// --- OBJECT CREATION ---

function addTextLayer(text = "New Text", x = 100, y = 100) {
    const layer = {
        id: String(Date.now() + Math.random()),
        type: 'text',
        text: text,
        x: x,
        y: y,
        fontSize: 60,
        fontFamily: 'Outfit',
        fontWeight: '900',
        color: '#ffffff',
        opacity: 1,
        width: 0, // Calculated on render
        height: 0,
        rotation: 0
    };
    layers.push(layer);
    selectLayer(layer.id);
    saveState();
    render();
}

function addImageLayer(src) {
    const img = new Image();
    img.onload = () => {
        let w = img.width;
        let h = img.height;
        if (w > 600) { h *= 600 / w; w = 600; }

        const layer = {
            id: String(Date.now() + Math.random()),
            type: 'image',
            img: img,
            src: src,
            x: canvas.width / 2,
            y: canvas.height / 2,
            width: w,
            height: h,
            opacity: 1,
            rotation: 0
        };
        layers.push(layer);
        selectLayer(layer.id);
        saveState();
        render();
    };
    img.src = src;
}

function addShapeLayer(type) {
    const layer = {
        id: String(Date.now() + Math.random()),
        type: 'shape',
        shapeType: type,
        x: canvas.width / 2,
        y: canvas.height / 2,
        width: 200,
        height: 200,
        color: '#6366f1',
        opacity: 1,
        rotation: 0
    };
    layers.push(layer);
    selectLayer(layer.id);
    saveState();
    render();
}

function deleteLayer() {
    if (!selectedId) return;
    layers = layers.filter(l => l.id !== selectedId);
    selectedId = null;
    saveState();
    render();
}

function moveLayer(dir) {
    const idx = layers.findIndex(l => l.id === selectedId);
    if (idx === -1) return;

    if (dir === 'up' && idx < layers.length - 1) {
        [layers[idx], layers[idx + 1]] = [layers[idx + 1], layers[idx]];
    } else if (dir === 'down' && idx > 0) {
        [layers[idx], layers[idx - 1]] = [layers[idx - 1], layers[idx]];
    }

    saveState();
    render();
}

async function saveDesign() {
    const username = localStorage.getItem('beast_user') || 'Guest';
    const dataURL = canvas.toDataURL('image/png');

    showToast("Saving your beast design...");

    try {
        const response = await fetch('/api/save-design', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                image: dataURL,
                name: 'beast_' + Date.now()
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            showToast("Design Saved to Gallery!");
        }
    } catch (e) {
        const link = document.createElement('a');
        link.download = 'beast-design.png';
        link.href = dataURL;
        link.click();
        showToast("Downloaded to your device!");
    }
}

// --- SELECTION & INTERACTION ---

function handleMouseDown(e) {
    const { x, y } = getMousePos(e);

    // 1. Check if clicking handles of selected object
    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        if (layer && !layer.locked) {
            const handle = getHandleAt(x, y, layer);
            if (handle) {
                isResizing = true;
                activeHandle = handle;
                return;
            }
        }
    }

    // 2. Check hit-detection for layers (top to bottom)
    const hitLayer = [...layers].reverse().find(l => !l.hidden && isPointInLayer(x, y, l));

    if (hitLayer) {
        selectLayer(hitLayer.id);
        if (!hitLayer.locked) {
            isDragging = true;
            dragStartX = x - hitLayer.x;
            dragStartY = y - hitLayer.y;
        }
    } else {
        selectedId = null;
        render();
    }
}

function getHandleAt(x, y, l) {
    const hw = l.width / 2;
    const hh = l.height / 2;
    const handles = {
        'se': [l.x + hw, l.y + hh],
        'sw': [l.x - hw, l.y + hh],
        'ne': [l.x + hw, l.y - hh],
        'nw': [l.x - hw, l.y - hh]
    };

    for (const [key, [hx, hy]] of Object.entries(handles)) {
        if (Math.abs(x - hx) < 15 && Math.abs(y - hy) < 15) return key;
    }
    return null;
}

function handleMouseMove(e) {
    if (!isDragging && !isResizing) {
        // Just update cursor
        updateCursor(e);
        return;
    }

    const { x, y } = getMousePos(e);
    const layer = layers.find(l => l.id === selectedId);
    if (!layer) return;

    if (isDragging) {
        layer.x = x - dragStartX;
        layer.y = y - dragStartY;
        applySnapping(layer);
    } else if (isResizing) {
        resizeLayer(layer, x, y);
    }

    render();
}

function handleMouseUp() {
    if (isDragging || isResizing) saveState();
    isDragging = false;
    isResizing = false;
    activeHandle = null;
}

function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    const scale = canvas.width / rect.width;
    return {
        x: (e.clientX - rect.left) * scale,
        y: (e.clientY - rect.top) * scale
    };
}

function isPointInLayer(px, py, l) {
    // Basic rect hit detection (Can be expanded with rotation support)
    const halfW = l.width / 2;
    const halfH = l.height / 2;
    return px >= l.x - halfW && px <= l.x + halfW &&
        py >= l.y - halfH && py <= l.y + halfH;
}

function resizeLayer(l, mx, my) {
    const dx = mx - l.x;
    const dy = my - l.y;

    if (activeHandle === 'se') {
        l.width = Math.abs(dx) * 2;
        l.height = Math.abs(dy) * 2;
    } else if (activeHandle === 'ne') {
        l.width = Math.abs(dx) * 2;
        l.height = Math.abs(dy) * 2;
    }
    // Simplistic scaling for demo, can be mapped per handle
}

// --- SNAPPING ENGINE ---

function applySnapping(layer) {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    if (Math.abs(layer.x - centerX) < SNAP_THRESHOLD) layer.x = centerX;
    if (Math.abs(layer.y - centerY) < SNAP_THRESHOLD) layer.y = centerY;
}

// --- RENDERING ENGINE ---

function render() {
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBackground();

    layers.forEach(layer => {
        if (layer.hidden) return; // SKIP HIDDEN

        ctx.save();
        ctx.globalAlpha = layer.opacity;
        ctx.translate(layer.x, layer.y);
        ctx.rotate(layer.rotation * Math.PI / 180);

        if (layer.type === 'text') {
            ctx.font = `${layer.fontWeight} ${layer.fontSize}px ${layer.fontFamily}`;
            ctx.fillStyle = layer.color;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(layer.text, 0, 0);

            const metrics = ctx.measureText(layer.text);
            layer.width = metrics.width + 20;
            layer.height = layer.fontSize * 1.2;
        } else if (layer.type === 'image') {
            ctx.drawImage(layer.img, -layer.width / 2, -layer.height / 2, layer.width, layer.height);
        } else if (layer.type === 'shape') {
            ctx.fillStyle = layer.color;
            if (layer.shapeType === 'rect') {
                ctx.fillRect(-layer.width / 2, -layer.height / 2, layer.width, layer.height);
            } else if (layer.shapeType === 'circle') {
                ctx.beginPath();
                ctx.ellipse(0, 0, layer.width / 2, layer.height / 2, 0, 0, Math.PI * 2);
                ctx.fill();
            } else if (layer.shapeType === 'triangle') {
                ctx.beginPath();
                ctx.moveTo(0, -layer.height / 2);
                ctx.lineTo(layer.width / 2, layer.height / 2);
                ctx.lineTo(-layer.width / 2, layer.height / 2);
                ctx.closePath();
                ctx.fill();
            }
        }

        ctx.restore();
    });

    if (selectedId) {
        const selLayer = layers.find(l => l.id === selectedId);
        if (selLayer && !selLayer.hidden) drawSelectionBox(selLayer);
    }

    if (showGrid) drawGrid();
    updateLayerPanel();
    syncPropertyPanel();
    if (window.lucide) lucide.createIcons();
}

function updateLayerPanel() {
    const list = document.getElementById('layer-list');
    if (!list) return;

    if (layers.length === 0) {
        list.innerHTML = '<div style="text-align: center; color: #64748b; font-size: 12px; margin-top: 40px;">No layers yet.</div>';
        return;
    }

    list.innerHTML = [...layers].reverse().map(l => `
        <div class="layer-item ${l.id === selectedId ? 'active' : ''}" onclick="selectLayer('${l.id}')" 
             style="background: ${l.id === selectedId ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.03)'}; 
                    padding: 10px; border-radius: 8px; display: flex; align-items: center; gap: 10px; cursor: pointer; border: 1px solid ${l.id === selectedId ? 'var(--primary)' : 'transparent'}">
            <i data-lucide="${l.type === 'text' ? 'type' : (l.type === 'image' ? 'image' : 'shapes')}" size="14"></i>
            <span style="font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${l.type === 'text' ? l.text : l.type}
            </span>
            <div style="display: flex; gap: 5px;">
                <i data-lucide="${l.locked ? 'lock' : 'unlock'}" size="12" style="opacity: 0.5"></i>
                <i data-lucide="${l.hidden ? 'eye-off' : 'eye'}" size="12" style="opacity: 0.5"></i>
            </div>
        </div>
    `).join('');
}

function toggleGrid() {
    showGrid = !showGrid;
    render();
    showToast(showGrid ? "Grid Enabled" : "Grid Disabled");
}

function drawGrid() {
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;

    for (let x = 0; x <= canvas.width; x += gridSpacing) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += gridSpacing) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
    ctx.restore();
}

function drawBackground() {
    ctx.fillStyle = '#1e293b'; // App default BG sync
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawSelectionBox(l) {
    ctx.save();
    ctx.translate(l.x, l.y);
    ctx.rotate(l.rotation * Math.PI / 180);

    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    const hw = l.width / 2;
    const hh = l.height / 2;

    ctx.strokeRect(-hw - 4, -hh - 4, l.width + 8, l.height + 8);

    // Draw Resize Handles
    ctx.fillStyle = '#ffffff';
    const handles = [
        [-hw - 4, -hh - 4], [hw + 4, -hh - 4], [-hw - 4, hh + 4], [hw + 4, hh + 4]
    ];
    handles.forEach(([hx, hy]) => {
        ctx.fillRect(hx - 4, hy - 4, 8, 8);
        ctx.strokeRect(hx - 4, hy - 4, 8, 8);
    });

    ctx.restore();
}

// --- UTILITIES ---

function selectLayer(id) {
    selectedId = String(id);
    render();
}

function syncPropertyPanel() {
    const propsPanel = document.getElementById('properties-panel');
    const sel = layers.find(l => l.id === selectedId);

    if (!sel || !propsPanel) {
        if (propsPanel) propsPanel.style.display = 'none';
        return;
    }

    propsPanel.style.display = 'block';

    // Sync Text Control
    const textInput = document.getElementById('prop-text');
    if (textInput && sel.type === 'text') {
        textInput.parentElement.style.display = 'block';
        textInput.value = sel.text;
    } else if (textInput) {
        textInput.parentElement.style.display = 'none';
    }

    // Sync Color
    const colorInput = document.getElementById('prop-color');
    if (colorInput) colorInput.value = sel.color || '#ffffff';

    // Sync Font Size
    const sizeInput = document.getElementById('prop-size');
    if (sizeInput && sel.type === 'text') {
        sizeInput.value = sel.fontSize;
    }
}

function updateObject(key, value) {
    const sel = layers.find(l => l.id === selectedId);
    if (!sel) return;

    if (key === 'fontSize' || key === 'opacity') value = parseFloat(value);
    sel[key] = value;

    render();
}

function updateOpacity(val) {
    updateObject('opacity', val);
}

let clipboardLayer = null;

function setBeastPreset(ratio) {
    let w, h;
    if (ratio === '16:9') { w = 1280; h = 720; }
    else if (ratio === '1:1') { w = 1080; h = 1080; }
    else if (ratio === '9:16') { w = 720; h = 1280; }

    resizeCanvas(w, h);
    showToast(`Canvas resized to ${ratio}`);
}

function handleKeyDown(e) {
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedId) {
            layers = layers.filter(l => l.id !== selectedId);
            selectedId = null;
            saveState();
            render();
        }
    }

    if (e.ctrlKey) {
        if (e.key === 'z') { historyUndo(); e.preventDefault(); }
        if (e.key === 'd') { duplicateLayer(); e.preventDefault(); }
        if (e.key === 'c') { copyLayer(); e.preventDefault(); }
        if (e.key === 'v') { pasteLayer(); e.preventDefault(); }
    }
}

function copyLayer() {
    if (!selectedId) return;
    const l = layers.find(l => l.id === selectedId);
    clipboardLayer = JSON.stringify(l);
    showToast("Layer Copied");
}

function pasteLayer() {
    if (!clipboardLayer) return;
    const data = JSON.parse(clipboardLayer);
    data.id = Date.now() + Math.random();
    data.x += 20;
    data.y += 20;
    layers.push(data);
    selectLayer(data.id);
    saveState();
    showToast("Layer Pasted");
}

function duplicateLayer() {
    if (!selectedId) return;
    const original = layers.find(l => l.id === selectedId);
    const copy = { ...original, id: Date.now() + Math.random(), x: original.x + 20, y: original.y + 20 };
    layers.push(copy);
    selectLayer(copy.id);
    saveState();
}

function saveState() {
    const state = JSON.stringify(layers);
    if (history[historyIndex] === state) return;
    history = history.slice(0, historyIndex + 1);
    history.push(state);
    historyIndex++;
}

function historyUndo() {
    if (historyIndex > 0) {
        historyIndex--;
        layers = JSON.parse(history[historyIndex]);
        // Re-hydrate images because JSON stringify loses them
        layers.forEach(l => {
            if (l.type === 'image') {
                l.img = new Image();
                l.img.src = l.src;
            }
        });
        render();
    }
}

function showToast(msg) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = '0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- UI MODALS ---

function openAIModal() {
    document.getElementById('ai-modal').style.display = 'flex';
}

function closeAIModal() {
    document.getElementById('ai-modal').style.display = 'none';
}

function openPricingModal() {
    document.getElementById('pricing-modal').style.display = 'flex';
}

function closePricingModal() {
    document.getElementById('pricing-modal').style.display = 'none';
}

// --- AI SYNC & LOGIC ---

async function syncUserStatus() {
    const username = localStorage.getItem('beast_user');
    if (!username || username === 'Guest') return;

    try {
        const res = await fetch(`/api/user-status?username=${encodeURIComponent(username)}`);
        if (!res.ok) throw new Error("Sync failure");
        const data = await res.json();

        if (data.status === 'success') {
            localStorage.setItem('beast_credits', data.credits);
            localStorage.setItem('beast_plan', data.plan);
            updateUserUI();
        }
    } catch (e) {
        console.error("User sync failed, using local offline data.");
    }
}

function updateUserUI() {
    const credits = localStorage.getItem('beast_credits') || '0';
    const plan = localStorage.getItem('beast_plan') || 'FREE';

    const creditEl = document.getElementById('user-credits');
    const upgradeBtn = document.getElementById('upgrade-btn');

    if (creditEl) creditEl.textContent = credits;
    if (upgradeBtn) {
        upgradeBtn.textContent = plan === 'PRO' ? 'PRO PLAN' : (plan === 'BEAST' ? 'BEAST PLAN' : 'UPGRADE');
        if (plan !== 'FREE') upgradeBtn.style.background = 'linear-gradient(45deg, #f59e0b, #ef4444)';
    }
}

async function buyPlan(plan) {
    const username = localStorage.getItem('beast_user');
    showToast(`Initializing ${plan} Upgrade...`);

    try {
        const res = await fetch('/api/buy-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, plan })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`Welcome to ${plan}!`);
            syncUserStatus();
            closePricingModal();
        }
    } catch (e) { showToast("Payment simulation failed"); }
}

async function generateWithAI() {
    const prompt = document.getElementById('ai-prompt').value;
    const apiKey = document.getElementById('ai-api-key').value;
    const model = document.getElementById('ai-model').value;
    const username = localStorage.getItem('beast_user');

    if (!prompt) return showToast("Enter a prompt!");

    const btn = document.getElementById('ai-btn-text');
    btn.textContent = "GENERATING...";

    try {
        const response = await fetch('/api/generate-logo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, apiKey, model, username })
        });
        const data = await response.json();

        if (data.image) {
            addImageLayer(data.image);
            closeAIModal();
            syncUserStatus();
            showToast("AI Masterpiece Created!");
        } else {
            showToast(data.message || "Generation Failed");
        }
    } catch (err) {
        showToast("AI Connection Error");
    } finally {
        btn.textContent = "INITIALIZE GENERATION";
    }
}

// Magic Placeholders
function openMagicMedia() { switchTab('magic', document.querySelector('[onclick*="magic"]')); showToast("Magic Media Ready"); }
function triggerMagicWrite() { showToast("Magic Write activated (Beta)"); }
function triggerMagicSwitch() { showToast("Magic Switch enabled"); }
function triggerMagicMorph() { showToast("Magic Morph starting..."); }
function triggerMagicEraser() { showToast("Select object to erase"); }
function triggerMagicExpand() { showToast("Expanding canvas..."); }

function handleFileUpload(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (f) => addImageLayer(f.target.result);
        reader.readAsDataURL(file);
    }
}

// --- AUTH & SESSION ---
function checkAuth() {
    const user = localStorage.getItem('beast_user');
    const display = document.getElementById('user-display');

    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    if (display) display.textContent = user;
    updateUserUI();
}

function handleLogout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

// --- AI STUDIO (GEMINI POWERED) ---

async function generateAIStudioContent() {
    const topic = document.getElementById('ai-topic').value;
    const tool = document.getElementById('ai-tool-type').value;
    const btn = document.getElementById('ai-gen-btn');
    const loading = document.getElementById('ai-loading');
    const results = document.getElementById('ai-results-container');
    const list = document.getElementById('ai-output-list');

    if (!topic) return showToast("Bhai, topic toh batao!");

    btn.disabled = true;
    loading.style.display = 'block';
    results.style.display = 'none';

    try {
        const res = await fetch('/api/ai/magic-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, mode: tool.includes('logo') ? 'logo' : 'thumbnail' })
        });
        const data = await res.json();

        if (data.status === 'success') {
            list.innerHTML = data.ideas.map(idea => `
                <div class="tool-card" style="padding: 15px; background: rgba(255,255,255,0.05); margin-bottom: 10px; cursor: pointer;" 
                     onclick="addTextLayer('${idea.replace(/'/g, "\\'")}')">
                    <p style="font-size: 13px; margin: 0;">${idea}</p>
                    <small style="color: var(--primary); font-size: 10px;">Click to Add to Canvas</small>
                </div>
            `).join('');
            results.style.display = 'flex';
        }
    } catch (e) {
        showToast("AI is resting. Try again!");
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
        if (window.lucide) lucide.createIcons();
    }
}

function submitFounderSurvey() {
    const input = document.getElementById('survey-input').value;
    if (!input) return showToast("Share an idea first!");
    showToast("Reward Claimed! 50 Credits Added.");
    document.getElementById('survey-card').style.display = 'none';
    // Ideally call API here
}
