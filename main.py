import os
from dotenv import load_dotenv
from core.brain import UltronBrain

def main():
    print("Initializing Ultron...")
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("Error: GEMINI_API_KEY not found. Please update your .env file.")
        return

    try:
        brain = UltronBrain(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Ultron's Brain: {e}")
        return

    print("Ultron is online. Waiting for input...")
    
    while True:
        try:
            # For now, we use text input. Voice will be added in the voice module.
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Ultron shutting down...")
                break
                
            response = brain.process_input(user_input)
            print(f"Ultron: {response}")
            
        except KeyboardInterrupt:
            print("\nUltron shutting down...")
            break

if __name__ == "__main__":
    main()
