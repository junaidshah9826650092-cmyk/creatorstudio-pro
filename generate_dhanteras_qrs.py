import qrcode
import os
from PIL import Image

# Folder banane ke liye, jahan designs save honge
output_folder = "dhanteras_qrs"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Aapki website ka base link
base_url = "https://creatorstudio-pro.onrender.com/reward.html?gift="

# 5 Unique Dhanteras Color Themes
# Colors are mostly Gold, Deep Red, Orange, Black etc.
themes = [
    {
        "id": "01_Royal_Gold",
        "fill_color": "#FFD700", # Gold (QR pattern)
        "back_color": "#800000"  # Deep Maroon (Background)
    },
    {
        "id": "02_Diya_Night",
        "fill_color": "#FFC107", # Bright Yellow/Orange
        "back_color": "#0B1D51"  # Deep Navy Blue
    },
    {
        "id": "03_Modern_Dhanteras",
        "fill_color": "#FFB81C", # Metallic Gold
        "back_color": "#111111"  # Pure Black
    },
    {
        "id": "04_Tradition",
        "fill_color": "#8B0000", # Dark Red
        "back_color": "#FFA500"  # Orange
    },
    {
        "id": "05_Silver_Purple",
        "fill_color": "#C0C0C0", # Silver
        "back_color": "#4B0082"  # Indigo/Purple
    }
]

print("🎨 Shubh Dhanteras! Generating 5 Unique QR Codes...")

for i, theme in enumerate(themes, start=1):
    # Unique Link for each QR Code
    unique_link = f"{base_url}{i}"
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=5, 
        error_correction=qrcode.constants.ERROR_CORRECT_H, 
        box_size=12, 
        border=4
    )
    qr.add_data(unique_link)
    qr.make(fit=True)

    # Apply Dhanteras Colors
    img = qr.make_image(
        fill_color=theme["fill_color"], 
        back_color=theme["back_color"]
    )
    
    # Agar future me aap center me Diya ya Coin ka logo lagana chahe, 
    # Toh error_correction 'H' hone ke karan logo aaraam se center pe place ho jayega!
    
    # Save Image
    filepath = os.path.join(output_folder, f"Dhanteras_QR_{theme['id']}.png")
    
    # --- Make it PRETTY (Rounded & Logo) ---
    img = img.convert("RGBA")
    width, height = img.size
    
    # Logo size should be small enough (max 15-20%) to keep QR scannable
    logo_size = width // 6 
    logo_pos = ((width - logo_size)//2, (height - logo_size)//2)
    
    # Create a stylized 'V' for Vitox center logo
    logo = Image.new("RGBA", (logo_size, logo_size), (0,0,0,0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(logo)
    
    # Draw Background circle for logo
    draw.ellipse([0, 0, logo_size, logo_size], fill=theme["fill_color"])
    
    # Draw a BOLD V in the center
    # Note: Using default font, we just make it as large as possible
    draw.text((logo_size//3, logo_size//10), "V", fill=theme["back_color"], font=None, stroke_width=2) 
    
    img.paste(logo, logo_pos, logo)
    img.save(filepath)
    
    print(f"✅ Created FIXED PRETTY: {filepath} (Link: {unique_link})")

print(f"\n🎉 Sabhi 5 Premium QR codes '{output_folder}' folder me save ho gaye hain!")
