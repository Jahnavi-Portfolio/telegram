TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "browse_website",
            "description": "Scrapes text content from a given URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to scrape"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_docx_report",
            "description": "Creates a DOCX report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "filename": {"type": "string"}
                },
                "required": ["title", "content", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pdf_report",
            "description": "Creates a PDF report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "filename": {"type": "string"}
                },
                "required": ["title", "content", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_drive_folder",
            "description": "Creates a folder in Google Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_name": {"type": "string"}
                },
                "required": ["folder_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "upload_drive_file",
            "description": "Uploads a local file to Google Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "local_filename": {"type": "string"},
                    "folder_name": {"type": "string"}
                },
                "required": ["local_filename"]
            }
        }
    }
]
