import os
import sys
import threading
from dotenv import load_dotenv

# Fix for pythonw: Redirect prints to a log file instead of a missing console!
if sys.stdout is None or sys.stderr is None:
    log_file = open("ultron_background.log", "a", buffering=1)
    if sys.stdout is None: sys.stdout = log_file
    if sys.stderr is None: sys.stderr = log_file

from core.brain import UltronBrain
from core.voice import UltronVoice
from core.server import run_server
from core.sensors import start_sensors

def main():
    print("Initializing Ultron...")
    load_dotenv()
    
    start_sensors()
    
    # ── BOOT RECOVERY CHECK ───────────────────────────────────────────────────
    from core.state import load_checkpoint, audit_log, update_heartbeat
    checkpoint = load_checkpoint()
    if checkpoint:
        print(f"[RECOVERY] Interrupted Goal detected: G-{checkpoint['goal_id']} — {checkpoint['objective']}")
        print(f"[RECOVERY] Last checkpoint: {checkpoint['last_checkpoint']} | Status: {checkpoint['status']}")
        audit_log("RECOVERY_BOOT", {
            "goal_id": checkpoint["goal_id"],
            "objective": checkpoint["objective"],
            "last_step": checkpoint.get("current_step", 0)
        })
        update_heartbeat(status="RECOVERING", current_goal=checkpoint["objective"])

        # Auto-clear RECOVERING after 30s — Ultron can't resume mid-chat history anyway
        import threading
        def _auto_clear_recovery():
            import time
            time.sleep(30)
            from core.state import clear_checkpoint
            clear_checkpoint()
            update_heartbeat(status="OPERATIONAL", current_goal=None)
            print("[RECOVERY] Recovery window expired. Status: OPERATIONAL.")
        threading.Thread(target=_auto_clear_recovery, daemon=True).start()
    else:
        update_heartbeat(status="OPERATIONAL")
    # ─────────────────────────────────────────────────────────────────────────
    
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
    # daemon=False ensures the script doesn't instantly die if the main thread finishes!
    server_thread = threading.Thread(target=run_server, args=(brain, voice, 8000), daemon=False)
    server_thread.start()

    voice.speak("Ultron is online and ready.")
    print("\n==============================================")
    print(" WEB DASHBOARD: http://localhost:8000 ")
    print("==============================================\n")
    
    # Check if we have a terminal attached
    if sys.stdin and sys.stdin.isatty():
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
                        continue
                else:
                    # Text Mode
                    user_input = mode
                    
                response = brain.process_input(user_input)
                voice.speak(response)
                
            except KeyboardInterrupt:
                print("\n")
                voice.speak("Emergency shutdown initiated. Goodbye.")
                break
            except EOFError:
                # If input() fails silently, just wait forever so the server stays alive
                import time
                while True: time.sleep(3600)
    else:
        # Running in background mode, keep the main thread alive for the server
        try:
            server_thread.join()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
