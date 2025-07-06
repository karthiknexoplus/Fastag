import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(log_dir='logs', log_file='fastag.log'):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = RotatingFileHandler(
        os.path.join(log_dir, log_file), maxBytes=2*1024*1024, backupCount=5
    )
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(handler) 