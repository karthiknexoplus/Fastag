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

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True 