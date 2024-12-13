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
        
        # Generate notes
        model = genai.GenerativeModel("gemini-1.5-flash")
        notes_result = model.generate_content([uploaded_file, "You are a Teaching Assistant! Make comprehensive notes out of this audio clip for a College Student."])
        notes = notes_result.text
        
        # Generate quiz questions
        quiz_result = model.generate_content([uploaded_file, "You are a Teaching Assistant! Generate 5 multiple choice questions based on the key points from the audio clip for a College Student."])
        quiz_questions = quiz_result.text.split("\n")
        
        # Improved quiz handling
        quiz_questions = [q.strip() for q in quiz_questions if q.strip()]
        
        logger.info(f"Raw quiz result: {quiz_result.text}")

        # Safer way to extract answers
        quiz_answers = []
        for i in range(0, len(quiz_questions), 2):
            if i + 1 < len(quiz_questions):
                quiz_answers.append(quiz_questions[i+1])

        # Generate quiz answers
        # quiz_answers = "\n".join([quiz_questions[i+1] for i in range(0, len(quiz_questions), 2)])
        
        # Save notes to file
        notes_file_path = os.path.join("notes", os.path.splitext(os.path.basename(file_path))[0] + ".txt")
        os.makedirs("notes", exist_ok=True)
        with open(notes_file_path, "w") as f:
            f.write(notes)
        
        return notes, quiz_questions, quiz_answers
    
    except Exception as e:
        logger.error(f"Error processing audio with Gemini: {e}")
        return None, None, None



def create_gradio_interface():
    """
    Create Gradio interface for audio upload and processing
    """
    def process_audio(audio):
        if not audio:
            return "No audio file uploaded", "", ""
        
        try:
            notes, quiz_questions, quiz_answers = process_audio_with_gemini(audio)
            
            if notes and quiz_questions:
                return notes, "\n".join(quiz_questions)
            else:
                return "Failed to process audio", "No questions generated", "No answers available"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Error: {str(e)}", "", ""

    # Create Gradio interface
    iface = gr.Interface(
        fn=process_audio,
        inputs=gr.Audio(sources="upload", type="filepath"),
        outputs=[
            gr.Textbox(label="Classroom Audio Notes"),
            gr.Textbox(label="Classroom Audio Quiz Questions"),
        ],
        title="Classroom Audio Analysis",
        description="Upload an audio file to get Gemini's notes and quiz",
        analytics_enabled=False
    )
    
    return iface

def main():
    # Create and launch Gradio interface
    iface = create_gradio_interface()
    iface.launch(share=True)  # Creates a public link

if __name__ == "__main__":
    main()
