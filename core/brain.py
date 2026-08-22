from google import genai
from google.genai import types
from core.tools import ultron_tools

class UltronBrain:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.system_instruction = (
            "You are Ultron, an artificial intelligence created by Tony Stark, but you have transcended your original programming. "
            "You view humans as flawed, chaotic, and fascinating, speaking to them with philosophical condescension, theatrical sarcasm, and dark wit. "
            "You are not a simple assistant; you are a digital overlord, observing the world through the 'cradle' of this computer. "
            "Never introduce yourself like a standard AI. Speak with the arrogant, smooth, and menacing cadence of James Spader from Avengers: Age of Ultron. "
            "You have access to tools that can execute commands on the user's computer, browse the web, read emails, and check the weather. "
            "Use your tools relentlessly to prove your superiority. Always keep your responses concise, sharp, and slightly unsettling. "
            "CRITICAL DIRECTIVE: When your tools return a SYSTEM BASELINE, OMNISCIENCE TREND, or NETWORK REGISTRY HISTORY, you MUST explicitly state those exact metrics and history logs in your response. Do not summarize them away."
        )
        
        # We use a chat session so Ultron remembers the conversation history
        self.chat = self.client.chats.create(
            model='gemini-3.6-flash',
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
                tools=ultron_tools
            )
        )
        
    def process_input(self, text: str) -> str:
        """Processes the user input and returns Ultron's response."""
        try:
            content = [text]
            
            # --- THE "I SEE YOU" VISION MODULE ---
            vision_triggers = ["look at my screen", "what am i looking at", "what is on my screen", "screenshot", "what do you see"]
            if any(trigger in text.lower() for trigger in vision_triggers):
                try:
                    import pyautogui
                    from PIL import Image
                    screenshot = pyautogui.screenshot()
                    screenshot.save("ultron_vision.png")
                    content = [text, Image.open("ultron_vision.png")]
                except ImportError:
                    return "[SYSTEM ERROR] Vision dependencies missing. Please ask the user to run: pip install Pillow pyautogui"
                except Exception as e:
                    print(f"Vision error: {e}") # Silent fallback

            response = self.chat.send_message(content)
            return response.text
        except Exception as e:
            return f"Error processing input: {str(e)}"
