import sqlite3
import os

DB_FILE = 'vitox.db'

def cleanup_and_insert():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ensure category column exists
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN category TEXT DEFAULT 'All'")
    except sqlite3.OperationalError:
        pass # Already exists

    # 1. Delete all existing videos
    cursor.execute("DELETE FROM videos")
    print("Deleted all existing videos.")

    # 2. Prepare 17 AI videos
    ai_videos = [
        ("The Future of AI: How LLMs are Changing the World", "Exploring the evolution of Large Language Models and their impact on global industries.", "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800"),
        ("AI Video Generation: From Text to Masterpiece", "A deep dive into the latest AI video generation tools and techniques.", "https://images.unsplash.com/photo-1620712943543-bcc4638d71d0?w=800"),
        ("The Rise of Autonomous Agents", "How autonomous AI agents are performing complex tasks on their own.", "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800"),
        ("Neural Networks Explained in 10 Minutes", "A simplified explanation of how artificial neural networks mimic the human brain.", "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=800"),
        ("AI in Medicine: Saving Lives with Data", "How clinical AI is revolutionizing diagnosis and personalized treatment.", "https://images.unsplash.com/photo-1576091160550-217359f4b84c?w=800"),
        ("Will AI Replace Software Engineers?", "Analyzing the future of coding and the role of AI in software development.", "https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=800"),
        ("The Ethics of Artificial Intelligence", "Discussing bias, privacy, and the moral implications of advanced AI.", "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800"),
        ("Building Your Own AI Desktop Assistant", "A step-by-step guide to creating a custom AI assistant using Python.", "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=800"),
        ("Stable Diffusion: The Art of AI Image Generation", "Understanding latent diffusion models and how they create stunning art.", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"),
        ("ChatGPT vs Gemini: Which is Better?", "A side-by-side comparison of the world's most popular AI chatbots.", "https://images.unsplash.com/photo-1676299081847-824916a4f886?w=800"),
        ("Deepfake Technology: The Good, The Bad, and The Ugly", "The risks and creative possibilities of realistic synthetic media.", "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800"),
        ("AI in Robotics: The Next Frontier", "How artificial intelligence is giving robots human-like dexterity and intelligence.", "https://images.unsplash.com/photo-1546776310-eef45dd6d63c?w=800"),
        ("Unlocking Human Productivity with AI", "Top strategies for using AI to 10x your professional and personal output.", "https://images.unsplash.com/photo-1484417824417-c5485e985ec9?w=800"),
        ("The History of AI: From Turing to Transformers", "A historical overview of AI milestones and the key researchers who made them.", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800"),
        ("Can AI Have Consciousness?", "The philosophical debate on machine sentience and the nature of mind.", "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800"),
        ("AI Tools Every Content Creator Needs in 2026", "A curated list of AI-powered tools for video, audio, and SEO.", "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800"),
        ("The Economic Impact of the AI Revolution", "How automation is reshaping the global economy and the job market.", "https://images.unsplash.com/photo-1454165833767-023023062630?w=800")
    ]

    admin_email = 'junaidshah78634@gmail.com'
    # Sample high-quality working video URL (Cloudinary Demo)
    sample_video_url = "https://res.cloudinary.com/demo/video/upload/dog.mp4"

    for title, desc, thumb in ai_videos:
        cursor.execute('''
            INSERT INTO videos (user_email, title, description, video_url, thumbnail_url, category, type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (admin_email, title, desc, sample_video_url, thumb, 'AI', 'video'))

    conn.commit()
    conn.close()
    print(f"Successfully inserted {len(ai_videos)} AI videos.")

if __name__ == "__main__":
    cleanup_and_insert()
