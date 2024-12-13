import os
import google.generativeai as genai
from dotenv import load_dotenv
import gradio as gr
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Google Drive Setup (Optional)
GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')

def upload_to_google_drive(file_path, folder_id=None):
    """
    Upload a file to Google Drive
    :param file_path: Path to the local file
    :param folder_id: Optional specific folder ID in Google Drive
    :return: File metadata from Google Drive
    """
    try:
        # Load credentials
        creds = None
        if GOOGLE_DRIVE_CREDENTIALS_PATH and os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
            creds = Credentials.from_authorized_user_file(GOOGLE_DRIVE_CREDENTIALS_PATH)
        
        # Build Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # File metadata
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Upload file
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        return file.get('id')
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return None

def process_audio_with_gemini(file_path):
    """
    Process audio file using Gemini
    :param file_path: Path to the audio file
    :return: Gemini's description of the audio
    """
    try:
        # Upload file to Gemini
        uploaded_file = genai.upload_file(path=file_path)
        
        # Generate model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate content
        result = model.generate_content([uploaded_file, "Describe this audio clip"])
        
        return result.text
    except Exception as e:
        print(f"Error processing audio with Gemini: {e}")
        return None

def main():
    # Example file path (replace with your actual path)
    audio_title = input("Enter the name of the audio file name Completely: ")
    audio_file_path = f"input_audio/{audio_title}"
    
    # Optional: Specify a Google Drive folder ID if you want to upload there
    DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')  # Optional
    
    # Upload to Google Drive (optional)
    if DRIVE_FOLDER_ID:
        drive_file_id = upload_to_google_drive(audio_file_path, DRIVE_FOLDER_ID)
        print(f"File uploaded to Google Drive with ID: {drive_file_id}")
    
    # Process with Gemini
    gemini_description = process_audio_with_gemini(audio_file_path)
    
    if gemini_description:
        print("Gemini's Audio Description:")
        print(gemini_description)
    else:
        print("Failed to process audio")

if __name__ == "__main__":
    main()
