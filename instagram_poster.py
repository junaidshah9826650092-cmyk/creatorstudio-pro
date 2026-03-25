import asyncio
import os
import random
import time
from playwright.async_api import async_playwright

async def human_delay(min_sec=2, max_sec=5):
    delay = random.uniform(min_sec, max_sec)
    print(f"[{delay:.1f}s delay...]")
    await asyncio.sleep(delay)

async def upload_to_instagram(video_path, caption_path):
    print("🚀 Starting Instagram Automation...")
    
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file {video_path} not found.")
        return
        
    caption = ""
    if os.path.exists(caption_path):
        with open(caption_path, "r", encoding="utf-8") as f:
            caption = f.read()
    else:
        caption = "Vitox Update! 🌟 #vitox"

    user_data_dir = os.path.join(os.getcwd(), "instagram_session")
    
    async with async_playwright() as p:
        # Launch Chromium with persistent context to save cookies
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # We want it visible so it behaves normally
            viewport={"width": 1280, "height": 720},
            args=["--disable-blink-features=AutomationControlled"] # Basic anti-detection
        )
        
        page = await browser.new_page()
        
        print("🌐 Navigating to Instagram...")
        await page.goto("https://www.instagram.com/")
        await human_delay(3, 6)
        
        # Check if logged in. If we see the login form, auto-login
        if await page.locator("input[name='username']").count() > 0:
            print("⚠️ Not logged in! Attempting auto-login with provided credentials...")
            await human_delay(1, 2)
            await page.locator("input[name='username']").fill("aidevloped")
            await human_delay(1, 3)
            await page.locator("input[name='password']").fill("9329165787d")
            await human_delay(1, 2)
            await page.locator("button[type='submit']").click()
            
            print("⏳ Waiting for login to complete...")
            try:
                # Wait for either the "New post" icon OR the "Not Now" button for Save Info
                await page.wait_for_function(
                    "() => document.querySelector(\"svg[aria-label='New post']\") || document.body.innerText.includes('Not Now')",
                    timeout=30000
                )
                print("✅ Auto-Login successful! Session will be saved.")
                await human_delay(3, 5)
            except Exception as e:
                print(f"❌ Login taking too long or failed: {e}")
                await browser.close()
                return
                
        # Optional: Handle "Not Now" dialogs if they pop up
        try:
            if await page.get_by_text("Not Now").count() > 0:
                print(" Dismissing 'Not Now' popup...")
                await page.get_by_text("Not Now").first.click()
                await human_delay(2, 4)
        except Exception:
            pass

        print("✍️ Finding Create Post button...")
        try:
            # Click "Create" (Plus icon in sidebar)
            create_btn = page.locator("svg[aria-label='New post']").locator("..").locator("..")
            await create_btn.click()
            await human_delay(2, 4)
            
            # Start file upload
            print(f"📂 Uploading {video_path}...")
            async with page.expect_file_chooser() as fc_info:
                await page.get_by_text("Select from computer").click()
            file_chooser = await fc_info.value
            
            absolute_video_path = os.path.abspath(video_path)
            await file_chooser.set_files(absolute_video_path)
            await human_delay(3, 6)
            
            # The crop/ratio screen: Click "Next"
            print("➡️ Clicking Next (Ratio)...")
            await page.get_by_role("button", name="Next").click()
            await human_delay(2, 4)
            
            # The cover/trim screen: Click "Next"
            print("➡️ Clicking Next (Cover)...")
            await page.get_by_role("button", name="Next").click()
            await human_delay(2, 4)
            
            # The caption screen
            print("📝 Typing caption...")
            caption_input = page.locator("div[aria-label='Write a caption...']")
            await caption_input.click()
            # Type with a slight delay
            for char in caption:
                await page.keyboard.press(char)
                await asyncio.sleep(random.uniform(0.01, 0.05))
            
            await human_delay(2, 4)
            
            print("📤 Clicking Share...")
            await page.get_by_role("button", name="Share").click()
            
            print("⏳ Waiting for upload to complete (this may take a minute)...")
            await page.wait_for_selector("img[alt='Animated checkmark']", timeout=120000)
            
            print("✅ Post shared successfully!")
            await human_delay(3, 5)
            
        except Exception as e:
            print(f"❌ Automation failed during posting: {e}")

        print("🚪 Closing browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(upload_to_instagram("daily_video.mp4", "daily_caption.txt"))
