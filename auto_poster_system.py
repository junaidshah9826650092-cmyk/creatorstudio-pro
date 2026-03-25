import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

# Poster config
WIDTH, HEIGHT = 1080, 1920
OUTPUT_DIR = "qr_posters"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Vitox Logo drawing helper (same as previous fix but centered on white)
def draw_vitox_logo(logo_size):
    bg_size = logo_size + 40 # White padding around logo
    logo_bg = Image.new("RGBA", (bg_size, bg_size), (255,255,255,255))
    draw = ImageDraw.Draw(logo_bg)
    draw.ellipse([10, 10, bg_size-10, bg_size-10], fill="#FF0055") # Pinkish circle
    scale = (logo_size-20) / 64.0
    # Center offset
    ox, oy = 20, 20
    poly_pts = [
        (32 * scale + ox, 62 * scale + oy),
        (4 * scale + ox, 12 * scale + oy),
        (18 * scale + ox, 12 * scale + oy),
        (32 * scale + ox, 40 * scale + oy),
        (46 * scale + ox, 12 * scale + oy),
        (60 * scale + ox, 12 * scale + oy)
    ]
    draw.polygon(poly_pts, fill="#FFFFFF")
    return logo_bg

def create_clean_qr(url):
    qr = qrcode.QRCode(
        version=5, 
        error_correction=qrcode.constants.ERROR_CORRECT_H, 
        box_size=16, 
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    
    # Add logo
    width, height = img.size
    logo_size = int(width * 0.15) # 15% size
    logo = draw_vitox_logo(logo_size)
    l_w, l_h = logo.size
    img.paste(logo, ((width - l_w)//2, (height - l_h)//2), logo)
    return img

def create_poster(variant, heading, subtext, style, cta):
    print(f"🎨 Generating Poster Variant {variant}...")
    
    # Create Base
    if style == "clean":
        bg_color = (250, 250, 250)
        text_color = (0, 0, 0)
        sub_color = (100, 100, 100)
        btn_color = (255, 0, 85)
    elif style == "modern":
        bg_color = (18, 14, 43) # Deep dark purple
        text_color = (255, 255, 255)
        sub_color = (200, 200, 255)
        btn_color = (0, 200, 255) # Cyan neon
    else: # bold
        bg_color = (255, 215, 0) # Bright Yellow
        text_color = (0, 0, 0)
        sub_color = (40, 40, 40)
        btn_color = (0, 0, 0)

    poster = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(poster)
    
    # Fonts (Fallback to default scaled if TTF missing, but usually this is rough. 
    # For a real pro system, we'd bundle a TTF like Inter/Roboto. We'll simulate by loading default and letting text just be default for now, 
    # or if on Windows, try arial.ttf)
    try:
        font_head = ImageFont.truetype("arialbd.ttf", 90)
        font_sub = ImageFont.truetype("arial.ttf", 50)
        font_cta = ImageFont.truetype("arialbd.ttf", 60)
    except:
        font_head = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_cta = ImageFont.load_default()

    # Draw Heading
    # Note: anchor="md" doesn't always work robustly in older PIL, using textbbox
    def draw_centered_text(y, text, font, color):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = (WIDTH - (bbox[2] - bbox[0])) / 2
        except:
            tx = WIDTH//4 # fallback
        draw.text((tx, y), text, fill=color, font=font)

    draw_centered_text(250, heading, font_head, text_color)
    draw_centered_text(380, subtext, font_sub, sub_color)
    
    # Embed Clean QR
    url = f"https://creatorstudio-pro.onrender.com/api/qr/scan?variant={variant}"
    qr_img = create_clean_qr(url)
    
    # Resize QR to standard poster size (e.g. 800x800)
    qr_img = qr_img.resize((700, 700), Image.Resampling.LANCZOS)
    
    # Optional: Draw a subtle frame or shadow behind QR if modern/bold
    qr_x = (WIDTH - 700) // 2
    qr_y = 600
    if style in ["modern", "bold"]:
        draw.rounded_rectangle([qr_x-15, qr_y-15, qr_x+715, qr_y+715], radius=30, fill=(255,255,255))
    
    poster.paste(qr_img, (qr_x, qr_y))
    
    # CTA Button
    btn_y = 1500
    btn_w, btn_h = 600, 120
    btn_x = (WIDTH - btn_w) // 2
    draw.rounded_rectangle([btn_x, btn_y, btn_x+btn_w, btn_y+btn_h], radius=60, fill=btn_color)
    btn_text_color = (255,255,255) if style != "bold" else (255, 215, 0)
    draw_centered_text(btn_y + 25, cta, font_cta, btn_text_color)
    
    # Save
    path = os.path.join(OUTPUT_DIR, f"Poster_Variant_{variant}.png")
    poster.save(path)
    print(f"✅ Saved: {path}")

variants = [
    ("A", "🚀 FREE YouTube Tools", "Thumbnail + Logo in 1 Click", "clean", "📱 Scan & Try Now"),
    ("B", "😳 You're Missing This", "Create Thumbnails FREE", "modern", "👇 Scan Before Others Do"),
    ("C", "🔥 Try Before Others", "No Login Needed", "bold", "⚡ INSTANT ACCESS")
]

for v in variants:
    create_poster(*v)

print("\n🎉 Auto A/B Testing Poster Generation Complete! Posters saved to 'qr_posters/'")
