// ==========================================
// BEAST STUDIO - CANVA ENGINE (MULTI-LAYER)
// ==========================================

// Global State
let canvas, ctx;
let layers = []; // Array of objects {type, x, y, text, color, size, ...}
let selectedId = null;
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let showGrid = false;
let uploadedImg = null; // Background image

// Init
function initBeast() {
    canvas = document.getElementById('beast-canvas');
    if (!canvas) return; // Guard

    ctx = canvas.getContext('2d');

    // Set HD Resolution
    resizeCanvas(1920, 1080);

    // Setup Listeners
    setupCanvasEvents();

    // Initial Layer
    if (layers.length === 0) {
        addTextLayer('BEAST MODE');
        layers[0].size = 120;
    }

    lucide.createIcons();
    render();
}

function resizeCanvas(w, h) {
    canvas.width = w;
    canvas.height = h;
    canvas.style.width = '100%';
    canvas.style.height = 'auto'; // Keep aspect ratio
    render();
}

// ==========================================
// CORE LAYERS SYSTEM
// ==========================================

function addTextLayer(content = 'New Text') {
    const layer = {
        id: Date.now(),
        type: 'text',
        text: content,
        x: canvas.width / 2,
        y: canvas.height / 2,
        size: 80,
        color: '#ffffff',
        font: 'Outfit',
        weight: '800',
        width: 0, // Calculated on render
        height: 0
    };
    layers.push(layer);
    selectLayer(layer.id);
    render();
    showToast('Text Layer Added');
}

function selectLayer(id) {
    selectedId = id;
    const layer = layers.find(l => l.id === id);

    if (layer) {
        // Update UI controls
        document.getElementById('editor-text').value = layer.text;
        document.getElementById('size-slider').value = layer.size;
        document.getElementById('text-color').value = layer.color;
    }
    render();
}

// ==========================================
// RENDER ENGINE
// ==========================================

function render() {
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;

    // 1. Clear & Background
    ctx.clearRect(0, 0, w, h);
    drawBackground(w, h);

    // 2. Draw Layers
    layers.forEach(layer => {
        if (layer.type === 'text') {
            drawTextLayer(layer);
        }
    });

    // 3. Draw Selection Box
    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        if (layer) drawSelectionBox(layer);
    }

    // 4. Overlays
    if (showGrid) drawGridOverlay(w, h);
}

function drawBackground(w, h) {
    const bgType = document.getElementById('gradient-type').value;
    const color = document.getElementById('bg-color').value;

    if (bgType === 'linear') {
        let g = ctx.createLinearGradient(0, 0, w, h);
        g.addColorStop(0, color);
        g.addColorStop(1, '#000000');
        ctx.fillStyle = g;
    } else {
        ctx.fillStyle = color;
    }
    ctx.fillRect(0, 0, w, h);
}

function drawTextLayer(layer) {
    ctx.save();
    ctx.font = `${layer.weight} ${layer.size}px '${layer.font}'`;
    ctx.fillStyle = layer.color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Shadow
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 20;
    ctx.shadowOffsetX = 5;
    ctx.shadowOffsetY = 5;

    ctx.fillText(layer.text, layer.x, layer.y);

    // Measure for hit detection
    const metrics = ctx.measureText(layer.text);
    layer.width = metrics.width;
    layer.height = layer.size; // Approx

    ctx.restore();
}

function drawSelectionBox(layer) {
    const padding = 20;
    const w = layer.width + padding * 2;
    const h = layer.height + padding * 2;

    ctx.save();
    ctx.strokeStyle = '#6366f1'; // Primary color
    ctx.lineWidth = 4;
    ctx.setLineDash([10, 5]);
    // Center alignment adjustment
    ctx.strokeRect(layer.x - w / 2, layer.y - h / 2, w, h);

    // Handles
    ctx.fillStyle = 'white';
    ctx.fillRect(layer.x - w / 2 - 6, layer.y - h / 2 - 6, 12, 12);
    ctx.fillRect(layer.x + w / 2 - 6, layer.y + h / 2 - 6, 12, 12);

    ctx.restore();
}

function drawGridOverlay(w, h) {
    ctx.save();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;

    // Rule of thirds
    ctx.beginPath();
    ctx.moveTo(w / 3, 0); ctx.lineTo(w / 3, h);
    ctx.moveTo(w * 2 / 3, 0); ctx.lineTo(w * 2 / 3, h);
    ctx.moveTo(0, h / 3); ctx.lineTo(w, h / 3);
    ctx.moveTo(0, h * 2 / 3); ctx.lineTo(w, h * 2 / 3);
    ctx.stroke();
    ctx.restore();
}

// ==========================================
// INTERACTIVTY (DRAG & DROP)
// ==========================================

function setupCanvasEvents() {
    // Mouse
    canvas.addEventListener('mousedown', handleStart);
    canvas.addEventListener('mousemove', handleMove);
    canvas.addEventListener('mouseup', handleEnd);
    // Touch
    canvas.addEventListener('touchstart', (e) => handleStart(e.touches[0]));
    canvas.addEventListener('touchmove', (e) => { e.preventDefault(); handleMove(e.touches[0]); });
    canvas.addEventListener('touchend', handleEnd);
}

function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
    };
}

function handleStart(e) {
    const pos = getCanvasCoords(e);

    // Check Hit (Reverse order for top-most first)
    // Simple box hit detection
    const clickedId = layers.slice().reverse().find(l => {
        const halfW = l.width / 2 + 20; // + padding
        const halfH = l.height / 2 + 20;
        return (pos.x >= l.x - halfW && pos.x <= l.x + halfW &&
            pos.y >= l.y - halfH && pos.y <= l.y + halfH);
    })?.id;

    if (clickedId) {
        selectLayer(clickedId);
        isDragging = true;
        dragStart = pos;
    } else {
        selectedId = null;
        render(); // Clear selection
    }
}

function handleMove(e) {
    if (!isDragging || !selectedId) {
        // Cursor management
        const pos = getCanvasCoords(e);
        const hovering = layers.some(l => {
            const halfW = l.width / 2 + 20;
            const halfH = l.height / 2 + 20;
            return (pos.x >= l.x - halfW && pos.x <= l.x + halfW &&
                pos.y >= l.y - halfH && pos.y <= l.y + halfH);
        });
        canvas.style.cursor = hovering ? 'move' : 'default';
        return;
    }

    const pos = getCanvasCoords(e);
    const dx = pos.x - dragStart.x;
    const dy = pos.y - dragStart.y;

    const layer = layers.find(l => l.id === selectedId);
    if (layer) {
        layer.x += dx;
        layer.y += dy;
        render();
    }

    dragStart = pos;
}

function handleEnd() {
    isDragging = false;
}

// ==========================================
// UI TABS SYSTEM
// ==========================================
function switchTab(tabName, element) {
    // 1. Update Rail Icons
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('active');
        el.querySelector('div').style.background = 'transparent';
        el.style.color = '#94a3b8';
    });

    // Activate clicked
    if (element) {
        element.classList.add('active');
        element.querySelector('div').style.background = 'rgba(255,255,255,0.05)';
        element.style.color = tabName === 'magic' ? '#fbbf24' : 'white';
    } else {
        // Fallback if called programmatically
        const target = document.querySelector(`.nav-item[onclick*="'${tabName}'"]`);
        if (target) {
            target.classList.add('active');
            target.querySelector('div').style.background = 'rgba(255,255,255,0.05)';
        }
    }

    // 2. Show Content Panel
    document.querySelectorAll('.panel-content').forEach(el => el.style.display = 'none');
    document.getElementById(`tab-${tabName}`).style.display = 'block';
}

// ==========================================
// UI BINDINGS
// ==========================================

// Typography Inputs
document.getElementById('editor-text').addEventListener('input', (e) => {
    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        layer.text = e.target.value;
        render();
    }
});

document.getElementById('size-slider').addEventListener('input', (e) => {
    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        layer.size = parseInt(e.target.value);
        render();
    }
});

document.getElementById('text-color').addEventListener('input', (e) => {
    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        layer.color = e.target.value;
        render();
    }
});

document.getElementById('bg-color').addEventListener('input', render);
document.getElementById('gradient-type').addEventListener('change', render);

document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');

        const type = chip.dataset.type;
        if (type === 'yt-thumb') resizeCanvas(1920, 1080);
        if (type === 'logo') resizeCanvas(1080, 1080);
        if (type === 'insta') resizeCanvas(1080, 1350);
        if (type === 'ios') resizeCanvas(1024, 1024);

        showToast('Canvas Resized: ' + type);
    });
});

// Helpers
function toggleGrid() {
    showGrid = !showGrid;
    render();
    showToast(showGrid ? "Grid ON" : "Grid OFF");
}

function showToast(msg) {
    let toast = document.getElementById('beast-toast');
    if (!toast) {
        // ... (Style same as before, injecting if needed or assume existent)
        toast = document.createElement('div');
        toast.id = 'beast-toast';
        toast.style.cssText = "position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#0f172a; color:white; padding:10px 20px; border-radius:50px; z-index:9999;";
        document.body.appendChild(toast);
    }
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 2000);
}

// ==========================================
// FILE UPLOADS SYSTEM
// ==========================================

// Hidden Input Change Listener (Add this element in HTML next step)
function handleFileUpload(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            addImageLayer(e.target.result);
            showToast("Image Uploaded Successfully");

            // Add to uploads gallery
            const gallery = document.getElementById('uploads-gallery');
            if (gallery) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.width = "48%";
                img.style.aspectRatio = "1";
                img.style.objectFit = "cover";
                img.style.borderRadius = "8px";
                img.style.cursor = "pointer";
                img.onclick = () => addImageLayer(e.target.result);
                gallery.appendChild(img);
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function addImageLayer(src) {
    const img = new Image();
    img.onload = () => {
        // Fit to canvas if too big
        let w = img.width;
        let h = img.height;
        if (w > 500) {
            const ratio = 500 / w;
            w = 500;
            h = h * ratio;
        }

        const layer = {
            id: Date.now(),
            type: 'image',
            img: img,
            x: canvas.width / 2,
            y: canvas.height / 2,
            width: w,
            height: h
        };
        layers.push(layer);
        selectLayer(layer.id);
        render(); // Needs drawImage update
    };
    img.src = src;
}

// Update Render for Images
function render() {
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;

    // 1. Background
    // ... (Keep existing background logic) ...
    ctx.clearRect(0, 0, w, h);
    drawBackground(w, h);

    // 2. Layers
    layers.forEach(layer => {
        if (layer.type === 'text') {
            drawTextLayer(layer);
        } else if (layer.type === 'image') {
            // Draw Image Centered
            ctx.save();
            ctx.drawImage(layer.img, layer.x - layer.width / 2, layer.y - layer.height / 2, layer.width, layer.height);
            ctx.restore();
        }
    });

    // 3. Selection
    if (selectedId) {
        const layer = layers.find(l => l.id === selectedId);
        if (layer) drawSelectionBox(layer);
    }

    if (showGrid) drawGridOverlay(w, h);
}

// MISSING MAGIC TOOLS
function triggerMagicEraser() {
    if (!selectedId) { showToast("Select an image to erase!"); return; }
    showToast("🧹 Eraser Tool Active (Simulated)");
    canvas.style.cursor = 'crosshair';
}

function triggerMagicExpand() {
    if (!selectedId) { showToast("Select an image to expand!"); return; }
    showToast("↔️ Expanding Image 16:9 (Simulated)");
    // Logic to upscale/outpaint would go here
}

// 1. Magic Media (Text to Image)
function openMagicMedia() {
    openAIModal(); // Reusing existing modal
    document.getElementById('ai-btn-text').innerText = "GENERATE MEDIA";
    showToast("Magic Media: Describe your image");
}

// 2. Magic Write (Contextual Copywriter)
async function triggerMagicWrite() {
    if (!selectedId) {
        showToast("Select text layer first!");
        return;
    }

    const layer = layers.find(l => l.id === selectedId);
    if (layer.type !== 'text') return;

    showToast("✨ Magic Write thinking...");

    // Simulate API call to Magic Write Endpoint
    // In production: fetch('api/ai/magic-text', { method: 'POST', body: JSON.stringify({ topic: layer.text, mode: 'slogan' }) })

    // Simulating "Context Aware" Rewrite
    const variants = [
        "Elevate Your Brand",
        "Design Future Now",
        "Ultimate Creator Tools",
        "Beast Mode Activated"
    ];

    // Fake typing effect
    setTimeout(() => {
        layer.text = variants[Math.floor(Math.random() * variants.length)];
        render();
        showToast("✨ text rewritten!");
    }, 1500);
}

// 6. Magic Switch (Multi-Format Engine)
function triggerMagicSwitch() {
    // Simulating "Layout Recognition"
    showToast("✨ Analyzing Layout...");

    setTimeout(() => {
        // Toggle between Square and Wide
        if (canvas.width === 1920) {
            resizeCanvas(1080, 1080); // Switch to Post
            showToast("Switched to Square Post (1:1)");
        } else {
            resizeCanvas(1920, 1080); // Switch to Thumbnail
            showToast("Switched to Thumbnail (16:9)");
        }

        // Auto Reposition Logic (Simple)
        layers.forEach(l => {
            l.x = canvas.width / 2;
            l.y = canvas.height / 2;
        });
        render();
    }, 1000);
}

// 7. Magic Morph (Texture & Effects)
function triggerMagicMorph() {
    if (!selectedId) {
        showToast("Select a layer to Morph!");
        return;
    }

    const layer = layers.find(l => l.id === selectedId);

    // Cycle through effects
    const effects = [
        { color: '#fbbf24', shadow: '#b45309', font: 'Outfit' }, // Gold
        { color: '#22d3ee', shadow: '#0891b2', font: 'Courier New' }, // Cyber
        { color: '#f472b6', shadow: '#be185d', font: 'Impact' },     // Pop
        { color: '#ffffff', shadow: '#000000', font: 'Outfit' }      // Reset
    ];

    const randomEffect = effects[Math.floor(Math.random() * effects.length)];

    showToast("✨ Applying Magic Texture...");

    layer.color = randomEffect.color;
    layer.font = randomEffect.font;
    // Note: Shadow logic is in render(), simplistic here

    render();
}

// Init
window.addEventListener('resize', () => {
    // Just re-render, don't reset
    const rect = canvas.getBoundingClientRect();
    // Maybe adjust CSS width? Already 100%
});
window.addEventListener('load', initBeast);
