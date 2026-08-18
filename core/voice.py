import os
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs import play

class UltronVoice:
    def __init__(self):
        # Initialize Speech-to-Text recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize ElevenLabs
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        # We will let you pick a specific Voice ID, but for now we default to a deep voice
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "cjVigY5qzO86Huf0OWal")
        
        if self.elevenlabs_api_key and self.elevenlabs_api_key != "your_elevenlabs_key_here":
            self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
        else:
            self.client = None
            print("[WARNING] ElevenLabs API Key not set in .env. Audio playback is disabled.")

    def speak(self, text: str):
        """Converts text to speech and plays it out loud."""
        print(f"Ultron: {text}")
        
        if not self.client:
            return
            
        try:
            audio = self.client.generate(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2"
            )
            play(audio)
        except Exception as e:
            print(f"[ElevenLabs Error: {e}]")

    def listen(self) -> str:
        """Listens to the microphone and returns the transcribed text."""
        with sr.Microphone() as source:
            print("\n[Listening... Speak now]")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("[Processing speech...]")
                
                text = self.recognizer.recognize_google(audio)
                print(f"You (Spoken): {text}")
                return text
                
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                print("[Speech unintelligible]")
                return ""
            except sr.RequestError as e:
                print(f"[Speech recognition service error: {e}]")
                return ""
