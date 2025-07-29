import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nexoplus@1234')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    # Use absolute path for database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'instance', 'fastag.db'))
    DEBUG = False
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '565920794982-jufd26bgd910efmfgasrnoqrc6bube15.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'GOCSPX-your-nexoplus@1234')
    
    # Feature flags
    FASTAG_FEATURES_ENABLED = os.environ.get('FASTAG_FEATURES_ENABLED', 'true').lower() == 'true'

    # VAPID keys
    VAPID_PRIVATE_KEY = None
    VAPID_PUBLIC_KEY = None
    VAPID_PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), '..', 'vapid_private.pem')
    VAPID_PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), '..', 'vapid_public.txt')
    try:
        with open(VAPID_PRIVATE_KEY_PATH, 'r') as f:
            VAPID_PRIVATE_KEY = f.read()
        with open(VAPID_PUBLIC_KEY_PATH, 'r') as f:
            VAPID_PUBLIC_KEY = f.read().strip()
    except Exception as e:
        raise RuntimeError(f"VAPID key files not found or unreadable. Please generate 'vapid_private.pem' and 'vapid_public.txt' in the project root. Error: {e}")

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True 