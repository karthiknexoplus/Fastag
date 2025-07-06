import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret-key')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    DB_PATH = os.environ.get('DB_PATH', os.path.join('instance', 'fastag.db'))
    DEBUG = False

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True 