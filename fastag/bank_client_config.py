import os

BANK_API_CONFIG = {
    'UAT': {
        'sync_time_url': 'https://uat-bank-url.example.com/sync_time',
        'heartbeat_url': 'https://uat-bank-url.example.com/heartbeat',
        'check_txn_url': 'https://uat-bank-url.example.com/checktxn',
        'tag_details_url': 'https://uat-bank-url.example.com/tagdetails',
        'pay_url': 'https://uat-bank-url.example.com/pay',
        'exceptionlist_url': 'https://uat-bank-url.example.com/exceptionlist',
        # Add other API URLs here
    },
    'PROD': {
        'sync_time_url': 'https://prod-bank-url.example.com/sync_time',
        'heartbeat_url': 'https://prod-bank-url.example.com/heartbeat',
        'check_txn_url': 'https://prod-bank-url.example.com/checktxn',
        'tag_details_url': 'https://prod-bank-url.example.com/tagdetails',
        'pay_url': 'https://prod-bank-url.example.com/pay',
        'exceptionlist_url': 'https://prod-bank-url.example.com/exceptionlist',
        # Add other API URLs here
    }
}

# Select environment: 'UAT' or 'PROD'
BANK_API_ENV = os.getenv('BANK_API_ENV', 'UAT')

# Usage example:
# from fastag.bank_client_config import BANK_API_CONFIG, BANK_API_ENV
# url = BANK_API_CONFIG[BANK_API_ENV]['sync_time_url'] 