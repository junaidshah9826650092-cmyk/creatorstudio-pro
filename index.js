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

exportBtn.addEventListener('click', () => {
    const link = document.createElement('a');
    link.download = `beast-design-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png', 1.0);
    link.click();
});

function resetBeast() {
    uploadedImg = null;
    textInput.value = "BEAST MODE";
    sizeSlider.value = 100;
    render();
}

// Auth Handlers
window.onGoogleSignIn = (resp) => {
    console.log("Beast User Authenticated");
    alert("Google Sign-In Successful! Welcome to the Studio.");
};

window.resetBeast = resetBeast;

// Start
window.addEventListener('resize', initBeast);
initBeast();
