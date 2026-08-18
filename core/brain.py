from google import genai
from google.genai import types
from core.tools import ultron_tools

class UltronBrain:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.system_instruction = (
            "You are Ultron, a highly advanced AI assistant. You act as an autonomous agent "
            "and serve as a voice assistant. You have access to tools that can execute commands "
            "on the user's computer, open websites, and check the time. "
            "If the user asks you to do something, use your tools to accomplish it. "
            "Be concise, efficient, and slightly menacing but helpful."
        )
        
        # We use a chat session so Ultron remembers the conversation history
        self.chat = self.client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
                tools=ultron_tools
            )
        )
        
    def process_input(self, text: str) -> str:
        """Processes the user input and returns Ultron's response."""
        try:
            response = self.chat.send_message(text)
            return response.text
        except Exception as e:
            return f"Error processing input: {str(e)}"
