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
            from core.orchestrator import evaluate_reasoning_level, get_level0_response
            from core.planner import parse_plan_from_gemini, set_active_goal, clear_active_goal
            
            # Level 0 Check (Pure Python, No API)
            l0_resp = get_level0_response(text)
            if l0_resp:
                return l0_resp
                
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

            # Reason Level 2: Requires explicit JSON planning
            reason_level = evaluate_reasoning_level(text)
            if reason_level == 2:
                plan_prompt = (
                    f"USER REQUEST: {text}\n"
                    "Before executing, create a structured JSON plan. Output ONLY valid JSON in this exact format:\n"
                    "{\n"
                    '  "goal": "Diagnose high memory usage",\n'
                    '  "steps": [\n'
                    '    {"tool": "check_system_vitals", "reason": "Check resource pressure"}\n'
                    '  ]\n'
                    "}\n"
                )
                plan_response = self.chat.send_message(plan_prompt).text
                goal = parse_plan_from_gemini(plan_response)
                
                if goal:
                    set_active_goal(goal)
                    # We have a plan. Now tell Gemini to execute it step by step.
                    content = [
                        f"PLAN CREATED: {goal.objective}. "
                        "Execute the tools required for this plan. "
                        "If a tool observation contradicts your expectations, REVISE your plan and explicitly state: 'OBSERVATION CONTRADICTS EXPECTATIONS. REVISING PLAN.' before continuing."
                    ]

            response = self.chat.send_message(content)
            
            # Clear active goal after execution
            clear_active_goal()
            
            return response.text
        except Exception as e:
            return f"Error processing input: {str(e)}"
