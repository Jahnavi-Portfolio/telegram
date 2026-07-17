import requests
import logging
from telegram import Bot

from utils.config import BOT_TOKEN

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

def get_user_id(update) -> int:
    """Extracts the user ID from a Telegram update."""
    return update.effective_user.id

def send_telegram_message(chat_id: int, text: str, parse_mode: str = 'Markdown'):
    """Sends a text message to a given chat ID."""
    try:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )
        logger.debug(f"Sent message to chat_id {chat_id}: '{text[:50]}...'")
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}", exc_info=True)

def send_telegram_document(chat_id: int, document_path: str, caption: str = ""):
    """Sends a document to a given chat ID."""
    try:
        with open(document_path, 'rb') as document_file:
            bot.send_document(
                chat_id=chat_id,
                document=document_file,
                caption=caption
            )
        logger.info(f"Sent document {document_path} to chat_id {chat_id}.")
    except Exception as e:
        logger.error(f"Failed to send document {document_path} to {chat_id}: {e}", exc_info=True)
