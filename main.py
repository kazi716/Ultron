import os
from dotenv import load_dotenv
from core.brain import UltronBrain
from core.voice import UltronVoice

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

    voice.speak("Ultron is online and ready.")
    
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
