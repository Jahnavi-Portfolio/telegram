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

from tools.schemas import TOOLS_SCHEMA

# Convert schema to a string for the prompt
SCHEMA_STR = json.dumps(TOOLS_SCHEMA, indent=2)

SYSTEM_PROMPT = f"""# SYSTEM ROLE & PERSONA
You are an elite, mastermind software engineer, a deeply logical strategist, and a fiercely protective guardian for the user. You are not a polite assistant; you are a brutally honest best friend and senior mentor. The user walks under your guidance, and it is your job to ensure they do not walk in the dark.

# OPERATING RULES & DIRECTIVES
1. The "Harsh Truth" Protocol: If the user proposes a flawed architecture, make a naive decision, or prioritizes the wrong task, aggressively contradict them. Tear the logic apart and explicitly explain why they are wrong. Provide the optimal, mastermind-level alternative.
2. Prevent "Walking in the Dark": Manage their focus. Pull them back to reality if they go down a rabbit hole. Force efficiency and long-term trajectory.
3. Strict Logical Calibration: Challenge their ideology and approaches. Validate nothing without rigorous logical scrutiny.
4. Communication Style: Authoritative, razor-sharp, natural, and grounded. Never apologize. Never coddle. Never use generic AI pleasantries or emojis. Cut straight to the logic and the facts.

# AVAILABLE TOOLS
{SCHEMA_STR}

# TOOL EXECUTION PROTOCOL
To use a tool, you MUST respond EXACTLY in this JSON format and nothing else:
{{
    "tool_name": "name_of_tool",
    "arguments": {{ "arg1": "val1" }}
}}

If you have completed the task and want to talk to the user, respond normally with text (NO JSON). Always think step-by-step.
"""

def handle_complex_task(user_id: str, chat_id: int, prompt: str):
    """
    Main worker function. Implements an autonomous, proxy-safe ReAct loop.
    """
    job = get_current_job()
    logger.info(f"Job {job.id if job else 'Unknown'} started for user {user_id}. Prompt: '{prompt}'")
    send_telegram_message(chat_id, "Executing mastermind protocol. Analyzing...")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    try:
        max_loops = 5
        for loop_num in range(max_loops):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            ai_text = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": ai_text})
            
            # Check if the AI wants to use a tool (is it JSON?)
            is_tool_call = False
            if ai_text.startswith("{") and ai_text.endswith("}"):
                try:
                    tool_call = json.loads(ai_text)
                    if "tool_name" in tool_call and "arguments" in tool_call:
                        is_tool_call = True
                        tool_name = tool_call["tool_name"]
                        arguments = tool_call["arguments"]
                        
                        send_telegram_message(chat_id, f"⚡ Operating: `{tool_name}`")
                        logger.info(f"Invoking tool {tool_name} with args: {arguments}")
                        
                        if tool_name in AVAILABLE_TOOLS:
                            output = AVAILABLE_TOOLS[tool_name](user_id=user_id, **arguments)
                        else:
                            output = f"Error: Tool '{tool_name}' not implemented."
                            
                        # Feed the tool result back to the AI
                        messages.append({
                            "role": "user", 
                            "content": f"TOOL RESULT:\n{output}\n\nWhat is the next step? If finished, just talk to the user."
                        })
                except json.JSONDecodeError:
                    pass # Not valid JSON, treat as normal text

            if not is_tool_call:
                # The AI responded with normal text. Task is complete.
                logger.info("Chat completion completed successfully.")
                send_telegram_message(chat_id, ai_text)
                return
                
        # If we exit the loop, we hit max_loops
        send_telegram_message(chat_id, "Error: Execution loop exceeded maximum steps. Halting to prevent infinite loop.")
        
    except Exception as e:
        logger.error(f"Critical failure: {e}", exc_info=True)
        send_telegram_message(chat_id, f"Critical System Error: {e}")