from typing import Dict, Optional, Any, IO
from io import BytesIO

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

from app.services.google_auth import GoogleAuthService
from datetime import datetime

class GoogleDriveService:
    """Service for interacting with Google Drive API"""

    @staticmethod
    def create_drive_service(access_token: str, refresh_token: Optional[str] = None, expiry: Optional[datetime] = None):
        """Create Google Drive API service"""
        credentials = GoogleAuthService.create_credentials(
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry
        )
        # Use Drive API v3
        return build('drive', 'v3', credentials=credentials)

    def __init__(self, access_token: str, refresh_token: Optional[str] = None, expiry: Optional[datetime] = None):
        """Initialize the Google Drive service"""
        self.service = self.create_drive_service(access_token, refresh_token, expiry)

    def download_file(self, file_id: str) -> Optional[BytesIO]:
        """Download a file from Google Drive by its ID"""
        try:
            # First, get file metadata to check the MIME type
            file_metadata = self.service.files().get(fileId=file_id, fields='mimeType, name').execute()
            mime_type = file_metadata.get('mimeType')
            print(f"Downloading file '{file_metadata.get('name')}' with MIME type: {mime_type}")

            request = None
            # Handle Google Docs, Sheets, Slides by exporting them
            if 'google-apps' in mime_type:
                if 'document' in mime_type:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
                elif 'spreadsheet' in mime_type:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
                # Add more export types if needed (e.g., PDF for presentations)
                else:
                    print(f"Unsupported Google Apps MIME type for export: {mime_type}")
                    return None
            else:
                # For other file types, use standard download
                request = self.service.files().get_media(fileId=file_id)

            if request:
                fh = BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}%.")
                fh.seek(0) # Reset stream position to the beginning
                return fh
            else:
                return None

        except HttpError as error:
            print(f"An error occurred downloading file {file_id}: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during download: {e}")
            return None

    def upload_file(
        self, 
        file_path: str, 
        file_name: str, 
        mime_type: str = 'application/pdf', 
        folder_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Upload a file to Google Drive"""
        try:
            file_metadata = {
                'name': file_name
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaIoBaseUpload(
                BytesIO(open(file_path, 'rb').read()), # Read file content into BytesIO
                mimetype=mime_type,
                resumable=True
            )
            
            # Perform the upload
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink' # Fields to return
            ).execute()
            
            print(f"File '{file.get('name')}' uploaded successfully with ID: {file.get('id')}")
            return file

        except HttpError as error:
            print(f"An error occurred uploading file {file_name}: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during upload: {e}")
            return None

    # Optional: Method to find or create a specific folder (e.g., "OpenCoder Submissions")
    def find_or_create_folder(self, folder_name: str) -> Optional[str]:
        """Find a folder by name, or create it if it doesn't exist. Returns folder ID."""
        try:
            # Search for the folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])

            if items:
                print(f"Found folder '{folder_name}' with ID: {items[0]['id']}")
                return items[0]['id']
            else:
                # Create the folder if not found
                print(f"Folder '{folder_name}' not found, creating...")
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=file_metadata, fields='id').execute()
                print(f"Created folder '{folder_name}' with ID: {folder.get('id')}")
                return folder.get('id')

        except HttpError as error:
            print(f"An error occurred finding or creating folder '{folder_name}': {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred with folder operation: {e}")
            return None