import os
from google.cloud import texttospeech
from django.conf import settings

# This tells the Google library where to find our key file, which we stored at the root of
# the backend/ directory. It builds the full absolute path from the project BASE_DIR.
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(settings.BASE_DIR, 'gcloud-credentials.json')

def produce_tts_audio(text_to_speak: str, output_path: str) -> str:
    """
    Generates an MP3 file from text using Google Cloud TTS.
    """

    print(f"TTS Service: Attempting to generate audio for text and save to {output_path}...")
    try:
        # Set up the client and input type.
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
        
        # Configure the voice.
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Standard-C",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = client.synthesize_speech(input=synthesis_input, voice=voice, 
                                            audio_config=audio_config)

        # Write the binary audio content to the specified output file.
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            
        print(f"TTS Service: Audio content written successfully to {output_path}")
        return output_path
    
    except Exception as e:
        print(f"TTS Service Error: {e}.")
        raise  # Re-raise the exception so the Celery task knows it failed.
