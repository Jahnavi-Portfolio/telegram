from telegram.ext import Application, CommandHandler, MessageHandler, filters

from utils.config import BOT_TOKEN, WEBHOOK_URL
from bot.handlers import start_command, handle_google_auth_code, default_handler, error_handler

# --- PTB Application Setup ---
ptb_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .updater(None)  # We use our own webserver, so no updater is needed
    .build()
)

# --- Register Handlers ---
# 1. /start command
ptb_app.add_handler(CommandHandler("start", start_command))

# 2. Google Auth Code Handler (a message that is not a command)
# This uses a simple regex to catch likely auth codes, but the real logic is in the handler.
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^[4]/[A-Za-z0-9\-_]+'), handle_google_auth_code))

# 3. Default message handler (for any other text)
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, default_handler))

# 4. Error handler
ptb_app.add_error_handler(error_handler)
