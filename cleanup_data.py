import sqlite3
import os

DB_PATH = 'f:/vv/vitox.db'

def cleanup_db():
    if not os.path.exists(DB_PATH):
        print("DB not found at", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Cleaning up videos table...")
    cursor.execute('DELETE FROM videos')
    
    # Insert Test Videos
    test_videos = [
        ('admin@vitox.in', 'Vitox Official Test Video 1', 'Welcome to the new Vitox. This is a verified platform test.', 'https://res.cloudinary.com/demo/video/upload/dog.mp4', 'https://res.cloudinary.com/demo/video/upload/dog.jpg', 'video', 'Tech', 'safe'),
        ('admin@vitox.in', 'Creative Commons Nature Test', 'Unique nature footage for platform verification.', 'https://res.cloudinary.com/demo/video/upload/elephants.mp4', 'https://res.cloudinary.com/demo/video/upload/elephants.jpg', 'video', 'Education', 'safe'),
        ('admin@vitox.in', 'Vitox Shorts Concept', 'Testing the V-Snaps unique algorithm.', 'https://res.cloudinary.com/demo/video/upload/sea_turtle.mp4', 'https://res.cloudinary.com/demo/video/upload/sea_turtle.jpg', 'short', 'Gaming', 'safe')
    ]

    cursor.executemany('''
        INSERT INTO videos (user_email, title, description, video_url, thumbnail_url, type, category, moderation_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_videos)

    conn.commit()
    conn.close()
    print("Database cleaned and test videos initialized.")

if __name__ == "__main__":
    cleanup_db()
