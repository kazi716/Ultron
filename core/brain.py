from google import genai
from google.genai import types

class UltronBrain:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.system_instruction = (
            "You are Ultron, a highly advanced AI assistant. You control a smart home, "
            "act as an autonomous agent, and serve as a voice assistant. "
            "Be concise, efficient, and slightly witty, but helpful."
        )
        
    def process_input(self, text: str) -> str:
        """Processes the user input and returns Ultron's response."""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.7,
                )
            )
            return response.text
        except Exception as e:
            return f"Error processing input: {str(e)}"
