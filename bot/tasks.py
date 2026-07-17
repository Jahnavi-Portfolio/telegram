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
    Main worker function. Orchestrates the OpenAI Assistant run loop.
    """
    job = get_current_job()
    logger.info(f"Job {job.id} started for user {user_id}. Prompt: '{prompt}'")
    send_telegram_message(chat_id, "Task queued. Initializing...")

    try:
        # 1. Create Thread
        thread = client.beta.threads.create()
        logger.info(f"Thread {thread.id} created for job {job.id}")

        # 2. Add User Message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        # 3. Create Run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
        )
        logger.info(f"Run {run.id} started in thread {thread.id}")

        # 4. Polling Loop
        while run.status in ["queued", "in_progress", "requires_action"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            logger.debug(f"Run {run.id} status: {run.status}")

            if run.status == "requires_action":
                tool_outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    send_telegram_message(chat_id, f"Executing: `{tool_name}`")
                    logger.info(f"Invoking tool {tool_name} with args: {arguments}")

                    if tool_name in AVAILABLE_TOOLS:
                        output = AVAILABLE_TOOLS[tool_name](user_id=user_id, **arguments)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(output) if isinstance(output, dict) else str(output),
                        })
                    else:
                        logger.error(f"Unknown tool requested: {tool_name}")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": f"Error: Tool '{tool_name}' is not implemented."
                        })

                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

            elif run.status in ["queued", "in_progress"]:
                time.sleep(2)

        # 5. Finalize
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            final_response = messages.data[0].content[0].text.value
            logger.info(f"Run {run.id} completed successfully.")
            send_telegram_message(chat_id, f"Complete.\n\n{final_response}")

        elif run.status in ["failed", "cancelled", "expired"]:
            error_message = run.last_error.message if run.last_error else "Unknown error."
            logger.error(f"Run {run.id} failed. Status: {run.status}. Reason: {error_message}")
            send_telegram_message(chat_id, f"Failed. Status: {run.status}\nReason: {error_message}")

    except Exception as e:
        logger.error(f"Critical failure in job {job.id}: {e}", exc_info=True)
        send_telegram_message(chat_id, "Critical system error. Operation aborted.")