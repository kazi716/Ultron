import pyttsx3
import speech_recognition as sr

class UltronVoice:
    def __init__(self):
        # Initialize Text-to-Speech engine
        self.engine = pyttsx3.init()
        
        # Configure the voice properties
        # rate: speed of speech
        self.engine.setProperty('rate', 175) 
        
        # Optionally, select a specific voice (0 is usually male, 1 is usually female on Windows)
        voices = self.engine.getProperty('voices')
        if len(voices) > 0:
            self.engine.setProperty('voice', voices[0].id)

        # Initialize Speech-to-Text recognizer
        self.recognizer = sr.Recognizer()

    def speak(self, text: str):
        """Converts text to speech and plays it out loud."""
        print(f"Ultron: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self) -> str:
        """Listens to the microphone and returns the transcribed text."""
        with sr.Microphone() as source:
            print("\n[Listening... Speak now]")
            # Adjust for background noise quickly
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                # Listen for the user's voice
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("[Processing speech...]")
                
                # Recognize using Google's free speech recognition
                text = self.recognizer.recognize_google(audio)
                print(f"You (Spoken): {text}")
                return text
                
            except sr.WaitTimeoutError:
                # No speech detected within the timeout
                return ""
            except sr.UnknownValueError:
                # Speech was detected but couldn't be understood
                print("[Speech unintelligible]")
                return ""
            except sr.RequestError as e:
                # Could not reach the recognition service
                print(f"[Speech recognition service error: {e}]")
                return ""
