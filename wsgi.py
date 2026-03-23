# wsgi.py
import sys
import os

# Add your project directory to the sys.path
path = '/home/yourusername/levy-platform'
if path not in sys.path:
    sys.path.append(path)

# Set the environment variable for Flask
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

# Import your app
from app import create_app

# Create the application instance
application = create_app()

if __name__ == '__main__':
    application.run()