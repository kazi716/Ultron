import os
import threading
from dotenv import load_dotenv
from core.brain import UltronBrain
from core.voice import UltronVoice
from core.server import run_server

def main():
    print("Initializing Ultron...")
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("Error: GEMINI_API_KEY not found. Please update your .env file.")
        return

    try:
        brain = UltronBrain(api_key=api_key)
        voice = UltronVoice()
    except Exception as e:
        print(f"Failed to initialize Ultron: {e}")
        return

    print("Starting Smart Hub Web Server on port 8000...")
    server_thread = threading.Thread(target=run_server, args=(brain, voice, 8000), daemon=True)
    server_thread.start()

    voice.speak("Ultron is online and ready.")
    print("\n==============================================")
    print(" WEB DASHBOARD: http://localhost:8000 ")
    print("==============================================\n")
    
    while True:
        try:
            mode = input("\nPress [Enter] to speak, or type your message (type 'exit' to quit): ")
            
            if mode.lower() in ['exit', 'quit']:
                voice.speak("Shutting down. Goodbye.")
                break
                
            if mode.strip() == "":
                # Voice Mode
                user_input = voice.listen()
                if not user_input:
                    continue # Skip if nothing was heard
            else:
                # Text Mode
                user_input = mode
                
            # Process with Gemini
            response = brain.process_input(user_input)
            
            # Speak and print response
            voice.speak(response)
            
        except KeyboardInterrupt:
            print("\n")
            voice.speak("Emergency shutdown initiated. Goodbye.")
            break

if __name__ == "__main__":
    main()
