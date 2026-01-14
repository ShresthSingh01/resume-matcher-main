import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")

class TTSManager:
    def __init__(self):
        print(f"DEBUG: Initializing TTSManager. API Key present: {bool(API_KEY)}")
        if API_KEY:
            self.client = ElevenLabs(api_key=API_KEY)
        else:
            self.client = None
            print("Warning: ELEVENLABS_API_KEY not found. TTS will not work.")

    def get_best_voice(self):
         # Try to find 'Adam', 'Josh' (US Male), 'Rachel' (US Female)
         try:
             all_voices = self.client.voices.get_all()
             
             for v in all_voices.voices:
                 if "Adam" in v.name or "Josh" in v.name: return v.voice_id
             
             for v in all_voices.voices:
                 if "Rachel" in v.name: return v.voice_id
                 
             return all_voices.voices[0].voice_id
         except:
             return "nPczCJZxpgCpKD07lhj7" # Fallback to hardcoded Brian

    def stream_audio(self, text: str):
        """
        Generates audio stream from text using ElevenLabs.
        Returns a generator yielding bytes.
        """
        if not self.client:
            raise ValueError("ElevenLabs API Key is missing.")

        try:
            voice_id = self.get_best_voice()
            # Updated for ElevenLabs v3+ SDK
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            
            for chunk in audio_stream:
                yield chunk
                
        except Exception as e:
            print(f"TTS Error: {e}")
            raise e
