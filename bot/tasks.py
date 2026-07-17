import os
import openai
import json
import time
import logging
from rq import get_current_job

from utils.config import OPENAI_API_KEY, OPENAI_API_BASE_URL, ASSISTANT_ID
from utils.telegram import send_telegram_message, send_telegram_document
from tools.browser import browse_website
from tools.report_generator import create_docx_report, create_pdf_report
from tools.google_drive import create_folder, upload_file

logger = logging.getLogger(__name__)

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE_URL)

# --- Tool Definitions ---
AVAILABLE_TOOLS = {
    "browse_website": browse_website,
    "create_docx_report": create_docx_report,
    "create_pdf_report": create_pdf_report,
    "create_drive_folder": create_folder,
    "upload_drive_file": upload_file,
}

def handle_complex_task(user_id: str, chat_id: int, prompt: str):
    """
    Main worker function. Uses standard Chat Completions for 9router.
    """
    job = get_current_job()
    logger.info(f"Job {job.id if job else 'Unknown'} started for user {user_id}. Prompt: '{prompt}'")
    send_telegram_message(chat_id, "Thinking...")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Note: 9router will likely automatically route this to their default model
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        final_response = response.choices[0].message.content
        logger.info(f"Chat completion completed successfully.")
        send_telegram_message(chat_id, final_response)

    except Exception as e:
        logger.error(f"Critical failure: {e}", exc_info=True)
        send_telegram_message(chat_id, f"Error: {e}")