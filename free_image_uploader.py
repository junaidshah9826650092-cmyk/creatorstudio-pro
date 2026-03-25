import os
import requests

def upload_to_catbox(image_path):
    print(f"🚀 Starting Catbox Upload for: {os.path.basename(image_path)}...")
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file {image_path} not found.")
        return False
        
    url = "https://catbox.moe/user/api.php"
    
    try:
        with open(image_path, "rb") as file:
            files = {
                'reqtype': (None, 'fileupload'),
                'fileToUpload': (os.path.basename(image_path), file, 'image/png')
            }
            response = requests.post(url, files=files)
            
            if response.status_code == 200:
                link = response.text.strip()
                print(f"✅ Success! Image uploaded to Catbox at: {link}")
                return link
            else:
                print(f"❌ Upload Failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception during Catbox upload: {e}")
        return False

def batch_upload_qrs():
    qr_dir = "dhanteras_qrs"
    if not os.path.exists(qr_dir):
        print(f"❌ Folder '{qr_dir}' not found.")
        return
        
    qr_files = [f for f in os.listdir(qr_dir) if f.endswith(".png")]
    if not qr_files:
        print("❌ No images found.")
        return
        
    print(f"Found {len(qr_files)} QR codes. Starting upload sequence...")
    
    results = []
    for qr_file in qr_files:
        path = os.path.join(qr_dir, qr_file)
        link = upload_to_catbox(path)
        if link:
            results.append(link)
            
    if results:
        print("\n--- Summary of Public Links ---")
        for link in results:
            print(link)
            
        with open("public_qr_links.txt", "w") as f:
            f.write("\n".join(results))
        print("\n✅ All links saved to public_qr_links.txt")
    else:
        print("\n❌ No images were uploaded.")

if __name__ == "__main__":
    batch_upload_qrs()
