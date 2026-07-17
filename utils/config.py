import os
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

# --- Core Bot Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("FATAL: BOT_TOKEN environment variable not set.")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("FATAL: WEBHOOK_URL environment variable not set. This is your app's public URL.")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- API Endpoints & Keys ---
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("FATAL: OPENAI_API_KEY environment variable not set.")

ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# --- Redis & RQ Config ---
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("FATAL: REDIS_URL environment variable not set.")

# --- Google OAuth Config ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
GOOGLE_AUTH_URI = os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")

if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID]):
    raise ValueError("FATAL: One or more Google OAuth environment variables are missing.")

# --- File Paths ---
# Create a .local directory for storing persistent data
LOCAL_DATA_DIR = ".local"
CREDENTIALS_DIR = os.path.join(LOCAL_DATA_DIR, "user_credentials")
OUTPUTS_DIR = os.path.join(LOCAL_DATA_DIR, "outputs")

os.makedirs(CREDENTIALS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
