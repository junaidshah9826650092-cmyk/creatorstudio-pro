from main import app as wsgi

# Ye file sirf Render ko dhokha dene ke liye hai
# Taaki 'gunicorn your_application.wsgi' kaam kar jaye
if __name__ == "__main__":
    wsgi.run()
