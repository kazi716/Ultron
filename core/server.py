from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import threading
import uvicorn
import os
from pydantic import BaseModel

app = FastAPI(title="Ultron Smart Hub")

# Global references to the core modules
ultron_brain = None
ultron_voice = None

class CommandRequest(BaseModel):
    command: str
    password: str = ""

class VerifyRequest(BaseModel):
    password: str

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the main web dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Error: static/index.html not found.</h1>")

@app.post("/api/verify")
async def verify_password(req: VerifyRequest):
    correct_password = os.getenv("ULTRON_PASSWORD", "ironman")
    if req.password != correct_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"status": "authorized"}

@app.post("/api/command")
async def process_command(request: CommandRequest):
    """Receives commands from the web UI and sends them to the Brain."""
    correct_password = os.getenv("ULTRON_PASSWORD", "ironman")
    if request.password != correct_password:
        return JSONResponse(content={"response": "ACCESS DENIED. INVALID CLEARANCE."})
        
    if not request.command or not ultron_brain:
        return JSONResponse({"response": "Error processing command."})
    
    # Send the command to Ultron's brain
    response_text = ultron_brain.process_input(request.command)
    
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
