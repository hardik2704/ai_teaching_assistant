import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import gradio as gr

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

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

def create_gradio_interface():
    """
    Create Gradio interface for audio upload and processing
    """
    def process_audio(audio):
        try:
            # Process the uploaded audio
            gemini_description = process_audio_with_gemini(audio)
            
            if gemini_description:
                return f"Gemini's Audio Description:\n{gemini_description}"
            else:
                return "Failed to process audio"
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
        print("This application only supports the web interface. Please choose 'web'.")
    elif interface_type == 'web':
        # Create and launch Gradio interface
        iface = create_gradio_interface()
        iface.launch(share=True)  # Creates a public link
    else:
        logger.warning("Invalid interface type. Please choose 'cli' or 'web'.")
        print("Invalid interface type. Please choose 'cli' or 'web'.")

if __name__ == "__main__":
    main()
