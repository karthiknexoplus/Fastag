import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logging(log_dir='logs', log_file='fastag.log'):
    """Setup logging with proper error handling for permission issues"""
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o755, exist_ok=True)
        
        # Ensure the logs directory has proper permissions
        try:
            os.chmod(log_dir, 0o755)
        except Exception as e:
            print(f"Warning: Could not set permissions on {log_dir}: {e}")
        
        log_file_path = os.path.join(log_dir, log_file)
        
        # Try to create the log file with proper permissions
        try:
            # Create empty log file if it doesn't exist
            if not os.path.exists(log_file_path):
                with open(log_file_path, 'w') as f:
                    pass
                os.chmod(log_file_path, 0o664)
        except Exception as e:
            print(f"Warning: Could not create log file {log_file_path}: {e}")
            # Fallback to console logging only
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                logger.addHandler(handler)
            return
        
        # Setup rotating file handler
        handler = RotatingFileHandler(
            log_file_path, maxBytes=2*1024*1024, backupCount=5
        )
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            logger.addHandler(handler)
            
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to console logging
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            logger.addHandler(handler) 