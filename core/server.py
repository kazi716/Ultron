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

@app.get("/api/logs")
async def get_logs():
    """Streams the background log file to the UI."""
    log_file = os.path.join(os.path.dirname(__file__), "..", "ultron_background.log")
    if not os.path.exists(log_file):
        return JSONResponse(content={"logs": "[SYSTEM] No background logs found."})
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            return JSONResponse(content={"logs": "".join(lines[-25:])})
    except Exception as e:
        return JSONResponse(content={"logs": f"[ERROR] Could not read logs: {e}"})

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

@app.get("/api/triggers")
async def get_triggers():
    """Returns any pending autonomous alerts from the sensor trigger queue."""
    from core.sensors import trigger_queue, incident_mode
    alerts = []
    while trigger_queue:
        alerts.append(trigger_queue.popleft())
    return JSONResponse({"alerts": alerts, "incident_mode": incident_mode})

@app.get("/api/heartbeat")
async def get_heartbeat_status():
    """Returns Ultron's current operational heartbeat and resource mode."""
    from core.state import get_heartbeat
    return JSONResponse(get_heartbeat())

@app.get("/api/audit")
async def get_audit_log():
    """Returns the last 15 entries from the immutable Audit Ledger."""
    from core.state import get_recent_audit
    return JSONResponse({"entries": get_recent_audit(15)})

def run_server(brain, voice, port=8000):
    """Starts the FastAPI server with references to the brain and voice."""
    global ultron_brain, ultron_voice
    ultron_brain = brain
    ultron_voice = voice
    # Run uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
