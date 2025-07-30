import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nexoplus@1234')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    # Use absolute path for database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'instance', 'fastag.db'))
    DEBUG = False
    
    # Session configuration for persistent login
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60  # 30 days
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '565920794982-jufd26bgd910efmfgasrnoqrc6bube15.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'GOCSPX-your-nexoplus@1234')
    
    # Feature flags
    FASTAG_FEATURES_ENABLED = os.environ.get('FASTAG_FEATURES_ENABLED', 'true').lower() == 'true'
    
    # PWA-only mode - when enabled, only PWA routes work
    PWA_ONLY_MODE = os.environ.get('PWA_ONLY_MODE', 'false').lower() == 'true'

    # VAPID keys
    VAPID_PRIVATE_KEY = None
    VAPID_PUBLIC_KEY = None
    VAPID_PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), 'vapid_private.pem')
    VAPID_PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), 'vapid_public.txt')
    
    print(f"Loading VAPID keys from: {VAPID_PRIVATE_KEY_PATH} and {VAPID_PUBLIC_KEY_PATH}")
    try:
        with open(VAPID_PRIVATE_KEY_PATH, 'r') as f:
            VAPID_PRIVATE_KEY = f.read()
            print("✓ VAPID private key loaded successfully")
        with open(VAPID_PUBLIC_KEY_PATH, 'r') as f:
            VAPID_PUBLIC_KEY = f.read().strip()
            print(f"✓ VAPID public key loaded: {VAPID_PUBLIC_KEY[:20]}...")
    except Exception as e:
        print(f"✗ Error loading VAPID keys: {e}")
        raise RuntimeError(f"VAPID key files not found or unreadable. Please generate 'vapid_private.pem' and 'vapid_public.txt' in the project root. Error: {e}")

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True 