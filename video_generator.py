import os
import random
import asyncio
import edge_tts
import g4f
import json
import re
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont

def get_ai_script():
    print("🤖 Prompting LLM for a fresh Vitox promo script...")
    
    prompt = """
    Write a short 3-sentence promotional script for a revolutionary new AI tool that generates "Ultra-Realistic High-Fidelity AI Faces" (High Face AI) perfect for video creators and influencers.
    The script MUST end exactly with: "Look closely, I've hidden a Dhanteras QR code somewhere in this video! Can you spot it? Scan it to unlock your secret gift!"
    Also provide a short 1-line catchy Instagram caption with emojis and hashtags like #AIFace #HighFaceAI #vitox #easteregg #dhanteras.
    
    Return the result EXACTLY and ONLY in this JSON format:
    {
       "title": "Short Title",
       "script": "The 3 sentences here",
       "caption": "The instagram caption here"
    }
    """
    
    try:
        # Use g4f to get a free LLM response
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo, # try generic model aliases that g4f rotates
            messages=[{"role": "user", "content": prompt}],
        )
        
        # Parse the JSON response
        clean_json = re.sub(r'```json\n?|\n?```', '', response).strip()
        data = json.loads(clean_json)
        return data
        
    except Exception as e:
        print(f"⚠️ LLM Generation failed ({e}). Using fallback script.")
        return {
            "title": "Vitox Secret",
            "script": "Attention creators! Vitox is the next big platform in India. I've hidden a special Dhanteras QR code somewhere in this video! Can you spot it? Scan it to unlock your secret gift!",
            "caption": "Can you find the hidden QR? 🕵️‍♂️ Scan it! #vitox #easteregg #dhanteras"
        }

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = line + word + " "
        try:
            length = draw.textlength(test_line, font=font)
        except AttributeError:
            length = draw.textlength(test_line) 
            
        if length > max_width:
            if line:
                lines.append(line.strip())
            line = word + " "
        else:
            line = test_line
    if line:
        lines.append(line.strip())
    return lines

def generate_background_image(title, text, output_path="temp_bg.png"):
    width, height = 1080, 1920
    img = Image.new('RGB', (width, height), color=(random.randint(5, 20), random.randint(10, 30), random.randint(30, 50))) 
    d = ImageDraw.Draw(img)
    
    title_font = None
    body_font = None
    
    font_paths = ["arialbd.ttf", "segoeui.ttf", "impact.ttf"]
    for fp in font_paths:
        try:
            title_font = ImageFont.truetype(fp, 100)
            break
        except IOError:
            continue
    
    font_paths = ["arial.ttf", "segoeui.ttf"]
    for fp in font_paths:
        try:
            body_font = ImageFont.truetype(fp, 65)
            break
        except IOError:
            continue
            
    if not title_font: title_font = ImageFont.load_default()
    if not body_font: body_font = ImageFont.load_default()
        
    d.text((100, 500), title, fill=(250, 204, 21), font=title_font)
    
    try:
        lines = wrap_text(text, body_font, 880, d)
        y_text = 750
        for line in lines:
            d.text((100, y_text), line, fill=(255, 255, 255), font=body_font)
            y_text += 90 
    except Exception as e:
        print(f"Warning: Text wrapping failed ({e}). Falling back to simple drawing.")
        d.text((100, 750), text, fill=(255, 255, 255), font=body_font)

    img.save(output_path)

async def generate_voiceover(text, output_path="temp_audio.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_path)

def create_video():
    print("🎬 Starting Vitox AI Video Generation Process...")
    
    # 1. Ask LLM for Script
    promo = get_ai_script()
    print(f"Selected Promo from AI: {promo['title']}")
    
    # 2. TTS
    print("🎙️ Generating Voiceover...")
    asyncio.run(generate_voiceover(promo['script']))
    
    # 3. Visuals
    print("🎨 Generating Visuals...")
    generate_background_image(promo['title'], promo['script'])
    
    # 4. Assembly & QR
    print("🎞️ Assembling Video with Hidden QR...")
    audio_clip = AudioFileClip("temp_audio.mp3")
    bg_clip = ImageClip("temp_bg.png").set_duration(audio_clip.duration)
    
    qr_dir = "dhanteras_qrs"
    qr_files = [f for f in os.listdir(qr_dir) if f.endswith(".png")]
    if not qr_files:
        print("❌ No QR codes found in 'dhanteras_qrs'.")
        return None
        
    qr_filename = os.path.join(qr_dir, random.choice(qr_files))
    print(f"🔍 Selected QR for hiding: {qr_filename}")
    
    qr_clip = ImageClip(qr_filename).resize(width=600)
    start_time = random.uniform(2.0, max(2.5, audio_clip.duration - 2.0))
    print(f"✨ Hiding QR code from {start_time:.1f}s to {start_time+0.5:.1f}s")
    
    qr_clip = qr_clip.set_start(start_time).set_duration(0.5).set_position("center")
    
    video = CompositeVideoClip([bg_clip, qr_clip])
    video = video.set_audio(audio_clip)
    
    output_filename = "daily_video.mp4"
    video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
    
    if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")
    if os.path.exists("temp_bg.png"): os.remove("temp_bg.png")
    
    with open("daily_caption.txt", "w", encoding="utf-8") as f:
        f.write(promo['caption'])
        
    print(f"✅ AI Video created successfully: {output_filename}")
    return output_filename

if __name__ == "__main__":
    create_video()
