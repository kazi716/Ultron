"""
ULTRON STATE MANAGER — Phase 4: Resilience & Survival
Handles:
  - Persistent Goal checkpointing (survives pythonw.exe crashes)
  - Boot-time recovery detection
  - Immutable Audit Ledger
"""

import json
import os
import time
import uuid
from typing import Optional

STATE_FILE = "ultron_state.json"
AUDIT_FILE = "ultron_audit.json"


# ─── GOAL CHECKPOINTING ───────────────────────────────────────────────────────

def save_checkpoint(goal) -> None:
    """
    Writes the current Goal state to disk.
    Called on every meaningful step transition — NOT every sensor tick.
    """
    if goal is None:
        clear_checkpoint()
        return

    steps = [
        {"tool": s.tool, "reason": s.reason, "status": s.status, "observation": s.observation}
        for s in goal.steps
    ]

    data = {
        "goal_id": goal.id,
        "objective": goal.objective,
        "status": goal.status.value,
        "current_step": goal.current_step,
        "created_at": goal.created_at,
        "last_checkpoint": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": steps,
        "recovery_policy": "RESUME_SAFE"
    }

    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def load_checkpoint() -> Optional[dict]:
    """
    Reads the persisted state file on boot.
    Returns the checkpoint dict if a recoverable Goal exists, else None.
    """
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        # Only resume if it was mid-execution
        if data.get("status") in ("EXECUTING", "REPLANNING", "PENDING"):
            return data
        return None
    except Exception:
        return None


def clear_checkpoint() -> None:
    """Clears the state file once a Goal completes or fails."""
    if os.path.exists(STATE_FILE):
        try:
            # Mark as COMPLETE rather than deleting, for audit purposes
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            data["status"] = "COMPLETE"
            data["last_checkpoint"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass


# ─── AUDIT LEDGER ────────────────────────────────────────────────────────────

def generate_action_id() -> str:
    """Generates a short unique Action ID like A-7F21."""
    return "A-" + str(uuid.uuid4())[:4].upper()


def audit_log(event_type: str, details: dict) -> str:
    """
    Appends an event to the immutable Audit Ledger.
    Returns the action_id for binding to UI approvals.
    """
    action_id = details.get("action_id", generate_action_id())
    entry = {
        "action_id": action_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        **details
    }

    ledger = []
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                ledger = json.load(f)
        except Exception:
            ledger = []

    ledger.append(entry)

    # Keep ledger lean — max 200 entries
    if len(ledger) > 200:
        ledger = ledger[-200:]

    try:
        with open(AUDIT_FILE, "w") as f:
            json.dump(ledger, f, indent=4)
    except Exception:
        pass

    return action_id


def get_recent_audit(n: int = 10) -> list:
    """Returns the last N audit entries."""
    if not os.path.exists(AUDIT_FILE):
        return []
    try:
        with open(AUDIT_FILE, "r") as f:
            ledger = json.load(f)
        return ledger[-n:]
    except Exception:
        return []


# ─── HEARTBEAT ────────────────────────────────────────────────────────────────

_heartbeat = {
    "status": "OPERATIONAL",
    "last_beat": time.strftime("%Y-%m-%d %H:%M:%S"),
    "current_goal": None,
    "last_tool": None,
    "last_error": None,
    "resource_mode": "NORMAL"
}


def update_heartbeat(**kwargs) -> None:
    """Updates the in-memory heartbeat state."""
    _heartbeat["last_beat"] = time.strftime("%Y-%m-%d %H:%M:%S")
    for k, v in kwargs.items():
        if k in _heartbeat:
            _heartbeat[k] = v


def get_heartbeat() -> dict:
    return dict(_heartbeat)
