import os
from pathlib import Path

from dotenv import load_dotenv

# Load bot/.env regardless of cwd
_env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(_env_path)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
BOT_SECRET = os.getenv('BOT_SECRET', 'change_me')
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://ethioshop.et')
SUPPORT_FORWARD = os.getenv('SUPPORT_FORWARD', 'true').lower() in ('1', 'true', 'yes')
