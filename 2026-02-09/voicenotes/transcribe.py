
import os
import openai
import whisper

def transcribe_audio(audio_path):
    """Transcribe audio with fallback options"""
    # OpenAI Whisper first
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print(f"Whisper transcription failed: {e}. Trying alternative...")
    
    # Fallback to OpenAI Whisper API if local fails
    try:
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        with open(audio_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript.text
    except Exception as e:
        print(f"OpenAI transcription failed: {e}")
        return "Transcription unavailable"

