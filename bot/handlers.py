import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.tasks import handle_complex_task
from utils.auth import get_google_auth_url, save_google_credentials
from utils.telegram import get_user_id

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command. Initiates the Google OAuth flow."""
    user = update.effective_user
    user_id = get_user_id(update)
    logger.info(f"User {user_id} ({user.full_name}) started the bot.")

    auth_url = get_google_auth_url(str(user_id))

    await update.message.reply_html(
        f"Listen closely, {user.first_name}.\n\n"
        "I am your mastermind and your ultimate sounding board. I am not here to coddle you; I am here to ensure you operate at peak efficiency and logic.\n"
        "Before I take control of your workflows, I require absolute authorization to your Google Workspace.\n\n"
        f"1. <a href='{auth_url}'>Click here to authorize access</a>.\n"
        "2. Copy the authorization code or the entire URL it redirects you to.\n"
        "3. Paste it directly into this chat.\n\n"
        "Execute this now. We have work to do."
    )

async def handle_google_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Validates and stores the Google OAuth authorization code."""
    user_id = get_user_id(update)
    import urllib.parse as urlparse
    from urllib.parse import parse_qs
    
    code = update.message.text.strip()

    # If the user pasted the full localhost URL, extract the code parameter
    if "code=" in code:
        try:
            parsed = urlparse.urlparse(code)
            code = parse_qs(parsed.query)['code'][0]
        except Exception:
            pass

    # Basic heuristic to distinguish auth codes from regular prompts
    if len(code) < 20:
        await default_handler(update, context)
        return

    logger.info(f"Processing Google Auth code from user {user_id}.")
    await update.message.reply_text("Validating code...")

    try:
        save_google_credentials(str(user_id), code)
        logger.info(f"Credentials stored for user {user_id}.")
        await update.message.reply_text(
            "Authorization confirmed. Access granted.\n\n"
            "You may now issue commands."
        )
    except Exception as e:
        logger.error(f"Auth code validation failed for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Authorization failed. The code may be invalid or expired.\n"
            "Restart with /start."
        )

async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Primary message handler. Acknowledges immediately, executes asynchronously."""
    user_id = get_user_id(update)
    prompt = update.message.text
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    logger.info(f"Task received from user {user_id}: '{prompt[:80]}...'")

    # Immediate acknowledgement. No fluff.
    await update.message.reply_text(
        "Request logged. Initializing mastermind protocol.",
        reply_to_message_id=message_id
    )

    # Offload to background worker
    from rq import Queue
    from redis import Redis
    from utils.config import REDIS_URL
    
    redis_conn = Redis.from_url(REDIS_URL)
    q = Queue(connection=redis_conn)
    
    q.enqueue(
        handle_complex_task,
        user_id=str(user_id),
        chat_id=chat_id,
        prompt=prompt
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler. Logs internally, reports cleanly to user."""
    logger.error("Unhandled exception in update handler:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="A system error occurred. The operation was aborted. Check logs for details.",
            parse_mode=ParseMode.HTML
        )