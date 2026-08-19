from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import threading
import uvicorn
import os

app = FastAPI(title="Ultron Smart Hub")

# Global references to the core modules
ultron_brain = None
ultron_voice = None

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the main web dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Error: static/index.html not found.</h1>")

@app.post("/api/command")
async def process_command(request: Request):
    """API endpoint to receive commands from the web dashboard."""
    data = await request.json()
    command = data.get("command", "")
    
    if not command or not ultron_brain:
        return JSONResponse({"response": "Error processing command."})
    
    # Send the command to Ultron's brain
    response_text = ultron_brain.process_input(command)
    
    # Speak the response out loud on the host PC in a background thread
    if ultron_voice:
        threading.Thread(target=ultron_voice.speak, args=(response_text,), daemon=True).start()
        
    return JSONResponse({"response": response_text})

def run_server(brain, voice, port=8000):
    """Starts the FastAPI server with references to the brain and voice."""
    global ultron_brain, ultron_voice
    ultron_brain = brain
    ultron_voice = voice
    # Run uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
