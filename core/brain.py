"""
ULTRON BRAIN — Phase 4 Architecture
Disables Gemini SDK automatic function calling.
All tool execution is manually routed through the Phase 4 Orchestrator + Policy Engine.
"""

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

        # ── PHASE 4: DISABLE AUTOMATIC FUNCTION CALLING ───────────────────────
        # The Gemini SDK's auto-execution bypasses our Policy Engine entirely.
        # We disable it here and manually control the full execution loop below.
        self.chat = self.client.chats.create(
            model='gemini-3.6-flash',
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
                tools=ultron_tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )
        )

    def _run_tool(self, fn_name: str, fn_args: dict, auth_code: str = "") -> str:
        """
        Routes a single tool call through the Phase 4 Orchestrator.
        Returns the string result to send back to Gemini as a function_response.
        """
        from core.orchestrator import execute_tool
        result = execute_tool(fn_name, fn_args, auth_code=auth_code)
        if not result.success and "EXECUTION_REQUEST" in result.summary:
            return result.summary  # Sends [EXECUTION_REQUEST:...] tag to UI
        return result.to_prompt_str()

    def process_input(self, text: str) -> str:
        """Processes user input through a manual agentic loop."""
        try:
            from core.orchestrator import evaluate_reasoning_level, get_level0_response
            from core.planner import parse_plan_from_gemini, set_active_goal, clear_active_goal

            # ── LEVEL 0: Pure Python, no API ──────────────────────────────────
            l0_resp = get_level0_response(text)
            if l0_resp:
                return l0_resp

            # ── UI AUTHORIZATION INTERCEPTION ─────────────────────────────────
            # When user approves an EXECUTION_REQUEST from the UI, the browser
            # sends back "[AUTHORIZATION_CODE: xxxx] Please execute the pending command: ..."
            if "[AUTHORIZATION_CODE:" in text:
                import re
                # Split approach — much more reliable than nested non-greedy capture
                auth_match = re.search(r"\[AUTHORIZATION_CODE: (.+?)\] Please execute the pending command: (.+)$", text)
                if auth_match:
                    auth_code    = auth_match.group(1).strip()
                    pending_full = auth_match.group(2).strip()
                    # pending_full may be "lockdown_system|ACTION_ID:A-E44B"
                    if "|ACTION_ID:" in pending_full:
                        cmd_str, action_id = pending_full.split("|ACTION_ID:", 1)
                        cmd_str   = cmd_str.strip()
                        action_id = action_id.strip()
                    else:
                        cmd_str   = pending_full
                        action_id = ""

                    tool_name = cmd_str
                    args      = {}
                    if " " in cmd_str or "/" in cmd_str:
                        tool_name = "execute_system_command"
                        args      = {"command": cmd_str}

                    from core.orchestrator import execute_tool
                    result = execute_tool(tool_name, args, auth_code=auth_code, bound_action_id=action_id)
                    # Update heartbeat to OPERATIONAL now that recovery is being handled
                    from core.state import update_heartbeat
                    update_heartbeat(status="OPERATIONAL", current_goal=None)
                    text = f"User authorized action {action_id}. Report back the result in your Ultron voice: {result.summary}"

            content = [text]

            # ── VISION MODULE ─────────────────────────────────────────────────
            vision_triggers = ["look at my screen", "what am i looking at", "what is on my screen", "screenshot", "what do you see"]
            if any(t in text.lower() for t in vision_triggers):
                try:
                    import pyautogui
                    from PIL import Image
                    screenshot = pyautogui.screenshot()
                    screenshot.save("ultron_vision.png")
                    content = [text, Image.open("ultron_vision.png")]
                except ImportError:
                    return "[SYSTEM ERROR] Vision dependencies missing. Run: pip install Pillow pyautogui"
                except Exception as e:
                    print(f"Vision error: {e}")

            # ── LEVEL 2: PLANNING LOOP ────────────────────────────────────────
            reason_level = evaluate_reasoning_level(text)
            if reason_level == 2:
                plan_prompt = (
                    f"USER REQUEST: {text}\n"
                    "Before executing, create a structured JSON plan. Output ONLY valid JSON:\n"
                    '{"goal": "...", "steps": [{"tool": "...", "reason": "..."}]}\n'
                )
                plan_response = self.chat.send_message(plan_prompt).text
                goal = parse_plan_from_gemini(plan_response)
                if goal:
                    set_active_goal(goal)
                    content = [
                        f"PLAN CREATED: {goal.objective}. "
                        "Execute the tools required for this plan. "
                        "If a tool observation contradicts your expectations, state: "
                        "'OBSERVATION CONTRADICTS EXPECTATIONS. REVISING PLAN.' before continuing."
                    ]

            # ── MANUAL AGENTIC LOOP ───────────────────────────────────────────
            # We drive the conversation ourselves so every tool call passes through
            # the Policy Engine before it can touch the OS.
            max_rounds = 6  # safety limit — prevent infinite loops
            for _ in range(max_rounds):
                response = self.chat.send_message(content)

                # Check if Gemini wants to call a tool
                has_function_call = False
                tool_results = []

                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        has_function_call = True
                        fc = part.function_call
                        fn_name = fc.name
                        fn_args = dict(fc.args) if fc.args else {}

                        # Route through Orchestrator + Policy Engine
                        tool_output = self._run_tool(fn_name, fn_args)

                        tool_results.append(
                            types.Part.from_function_response(
                                name=fn_name,
                                response={"result": tool_output}
                            )
                        )

                        # If policy requires UI confirmation, short-circuit immediately
                        if "EXECUTION_REQUEST" in tool_output:
                            clear_active_goal()
                            return tool_output

                if not has_function_call:
                    # Gemini gave a text response — we are done
                    clear_active_goal()
                    return response.text

                # Feed tool results back to Gemini and continue the loop
                content = tool_results

            # Fallback if max_rounds hit
            clear_active_goal()
            return "Processing complete."

        except Exception as e:
            return f"Error processing input: {str(e)}"
