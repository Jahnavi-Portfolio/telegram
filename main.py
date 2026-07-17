import os
import uvicorn
from fastapi import FastAPI, Request, Response
from http import HTTPStatus
from contextlib import asynccontextmanager
import logging

from telegram import Update
from bot.core import ptb_app, BOT_TOKEN, WEBHOOK_URL
from utils.config import LOG_LEVEL

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Set and delete the Telegram webhook on application startup and shutdown.
    """
    webhook_endpoint = f"{WEBHOOK_URL}/telegram"
    logger.info(f"Setting webhook for {webhook_endpoint}...")
    await ptb_app.bot.set_webhook(
        url=webhook_endpoint,
        allowed_updates=Update.ALL_TYPES,
        secret_token=BOT_TOKEN.split(":")[-1] # Use a part of the token as a simple secret
    )
    logger.info("Webhook successfully set.")

    async with ptb_app:
        await ptb_app.start()
        yield
        await ptb_app.stop()

    logger.info("Deleting webhook...")
    await ptb_app.bot.delete_webhook()
    logger.info("Webhook successfully deleted.")

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)

@app.post("/telegram")
async def telegram_webhook(request: Request) -> Response:
    """
    Handle incoming Telegram updates.
    """
    # Simple secret token validation
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != BOT_TOKEN.split(":")[-1]:
        logger.warning("Invalid secret token received.")
        return Response(status_code=HTTPStatus.UNAUTHORIZED)

    try:
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)
        await ptb_app.process_update(update)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for Render/Railway to probe.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
