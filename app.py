import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import gradio as gr
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
import google.auth.transport.requests

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Google Drive Scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_refresh_token():
    """
    Fetch refresh token from existing credentials
    """
    try:
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, SCOPES)
        credentials = flow.run_local_server(port=0)
        return credentials
    except Exception as e:
        logger.error(f"Error getting refresh token: {e}")
        return None

def get_google_drive_credentials():
    """Get Google Drive credentials using OAuth 2.0"""
    creds = None
    credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
    token_path = 'token.json'

    try:
        # Check if token exists
        if os.path.exists(token_path):
            logger.info("Existing token file found.")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            logger.info("No valid credentials found. Running OAuth flow.")
            
            # Handle expired credentials
            if creds and creds.expired and creds.refresh_token:
                logger.info("Credentials have expired. Attempting to refresh...")
                try:
                    # Create a request to refresh the credentials
                    request = google.auth.transport.requests.Request()
                    creds.refresh(request)
                except Exception as refresh_error:
                    logger.warning(f"Refresh failed: {refresh_error}")
                    # Fall back to full OAuth flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
            else:
                # Full OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            logger.info("Credentials saved successfully.")
        
        return creds
    
    except Exception as e:
        logger.error(f"Error in getting Google Drive credentials: {e}")
        return None

def upload_to_google_drive(file_path, folder_id=None):
    """
    Upload a file to Google Drive
    """
    try:
        # Get credentials
        creds = get_google_drive_credentials()
        
        if not creds:
            logger.error("Failed to obtain credentials")
            return None
        
        # Build Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # File metadata
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Upload file
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        logger.info(f"File uploaded successfully. File ID: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        logger.error(f"Error uploading to Google Drive: {e}")
        return None

def process_audio_with_gemini(file_path):
    """
    Process audio file using Gemini
    """
    try:
        # Upload file to Gemini
        uploaded_file = genai.upload_file(path=file_path)
        
        # Generate model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate content
        result = model.generate_content([uploaded_file, "You are a Teaching Assistant! Make comprehensive notes out of this audio clip for a College Student."])
        
        return result.text
    
    except Exception as e:
        logger.error(f"Error processing audio with Gemini: {e}")
        return None

def cli_process_audio():
    """
    Command-line interface for audio processing
    """
    # Example file path (replace with your actual path)
    audio_title = input("Enter the name of the audio file completely: ")
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

def create_gradio_interface():
    """
    Create Gradio interface for audio upload and processing
    """
    def process_audio(audio):
        try:
            # Process the uploaded audio
            gemini_description = process_audio_with_gemini(audio)
            
            # Optional: Upload to Google Drive
            drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            if drive_folder_id:
                drive_file_id = upload_to_google_drive(audio, drive_folder_id)
                return f"Gemini Description:\n{gemini_description}\n\nGoogle Drive File ID: {drive_file_id}"
            
            return gemini_description
        except Exception as e:
            logger.error(f"Error in Gradio audio processing: {e}")
            return f"Error: {str(e)}"

    # Create Gradio interface
    iface = gr.Interface(
        fn=process_audio,
        inputs=gr.Audio(sources="upload", type="filepath"),
        outputs=gr.Textbox(label="Classroom Audio Analysis"),
        title="Classroom Audio Analysis",
        description="Upload an audio file to get Gemini's description"
    )
    
    return iface

def main():
    # Ask user for interface type
    interface_type = input("Choose interface type (cli/web): ").lower()
    
    if interface_type == 'cli':
        cli_process_audio()
    elif interface_type == 'web':
        # Create and launch Gradio interface
        iface = create_gradio_interface()
        iface.launch(share=True)  # Creates a public link
    else:
        logger.warning("Invalid interface type. Please choose 'cli' or 'web'.")
        print("Invalid interface type. Please choose 'cli' or 'web'.")

if __name__ == "__main__":
    main()
