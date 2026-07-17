import os
import logging
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from utils.auth import get_google_service
from utils.config import OUTPUTS_DIR

logger = logging.getLogger(__name__)

def get_drive_service(user_id: str):
    """Helper to get an authorized Google Drive service client."""
    return get_google_service(user_id, 'drive', 'v3')

def create_folder(user_id: str, folder_name: str) -> str:
    """Creates a new folder in the root of the user's Google Drive."""
    logger.info(f"Attempting to create Drive folder '{folder_name}' for user {user_id}.")
    try:
        service = get_drive_service(user_id)
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata, fields='id, webViewLink').execute()
        folder_id = file.get('id')
        folder_link = file.get('webViewLink')
        logger.info(f"Successfully created folder '{folder_name}' with ID: {folder_id}")
        return f"Successfully created folder '{folder_name}'. You can view it here: {folder_link}"
    except HttpError as error:
        logger.error(f"An error occurred creating Drive folder: {error}")
        return f"Error: Failed to create folder. {error}"
    except Exception as e:
        logger.error(f"An unexpected error occurred in create_folder: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while creating the folder."

def upload_file(user_id: str, local_filename: str, folder_name: str = None) -> str:
    """Uploads a local file to a specified folder in Google Drive."""
    local_path = os.path.join(OUTPUTS_DIR, local_filename)
    if not os.path.exists(local_path):
        logger.error(f"Local file not found for upload: {local_path}")
        return f"Error: The file '{local_filename}' does not exist to be uploaded."

    logger.info(f"Attempting to upload '{local_filename}' to Drive for user {user_id}.")

    try:
        service = get_drive_service(user_id)
        folder_id = None

        if folder_name:
            # Find the folder ID from the folder name
            response = service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            folders = response.get('files', [])
            if not folders:
                logger.warning(f"Folder '{folder_name}' not found. Uploading to root.")
                # Optionally, create the folder if it doesn't exist
                # create_folder_response = create_folder(user_id, folder_name)
                # ... parse the ID from the response ...
            else:
                folder_id = folders[0].get('id')
                logger.info(f"Found folder '{folder_name}' with ID: {folder_id}")

        file_metadata = {
            'name': local_filename,
            'parents': [folder_id] if folder_id else []
        }
        media = MediaFileUpload(local_path, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        file_link = file.get('webViewLink')
        logger.info(f"Successfully uploaded file '{local_filename}'. Link: {file_link}")
        return f"Successfully uploaded '{local_filename}' to Google Drive. You can view it here: {file_link}"

    except HttpError as error:
        logger.error(f"An error occurred uploading file to Drive: {error}")
        return f"Error: Failed to upload file. {error}"
    except Exception as e:
        logger.error(f"An unexpected error occurred in upload_file: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while uploading the file."

