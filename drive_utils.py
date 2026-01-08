import os
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Scopes required for Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Service Account Key File
SERVICE_ACCOUNT_FILE = 'google_keys.json'

def authenticate_drive():
    """
    Authenticates with Google Drive API using service account credentials.
    Returns the Drive service object or None if failed.
    """
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        st.error(f"❌ Error: '{SERVICE_ACCOUNT_FILE}' not found. Please upload the key file.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"❌ Authentication Error: {e}")
        return None

def upload_file_to_drive(file_obj, filename, folder_id):
    """
    Uploads a file object (BytesIO) to a specific Google Drive folder.
    
    Args:
        file_obj: The file object (e.g., from st.camera_input or st.file_uploader)
        filename: Name to save the file as on Drive
        folder_id: The ID of the Google Drive folder
        
    Returns:
        The uploaded file ID if successful, None otherwise.
    """
    service = authenticate_drive()
    if not service:
        return None

    try:
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype='image/jpeg', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')
        
    except Exception as e:
        st.error(f"❌ Upload Error: {e}")
        return None
