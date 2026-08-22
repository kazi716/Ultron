"""
ULTRON ORCHESTRATOR — Phase 4 Upgrade
Adds: Action IDs, Retry Backoff, Audit Ledger binding, Heartbeat updates
"""

import time
import psutil
from dataclasses import dataclass, field
from typing import Any, Optional
from core.registry import TOOL_REGISTRY, get_tool
from core.policy import evaluate, PolicyDecision
from core.state import (
    audit_log, generate_action_id, update_heartbeat,
    save_checkpoint, get_heartbeat
)


@dataclass
class ToolResult:
    """Structured result returned by every tool call."""
    success: bool
    tool: str
    action_id: str = ""        # Unique ID bound to this specific execution
    timestamp: str = ""
    summary: str = ""
    data: dict = field(default_factory=dict)
    error: str = ""
    verification: str = ""
    confidence: float = 1.0

    def to_prompt_str(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"[ACTION: {self.action_id} | TOOL: {self.tool} | STATUS: {status} | CONFIDENCE: {int(self.confidence*100)}%]",
            f"Summary: {self.summary}",
        ]
        if self.data:
            for k, v in self.data.items():
                lines.append(f"  {k}: {v}")
        if self.error:
            lines.append(f"Error: {self.error}")
        if self.verification:
            lines.append(f"Verification: {self.verification}")
        return "\n".join(lines)


# ─── REASONING BUDGET ────────────────────────────────────────────────────────

def evaluate_reasoning_level(text: str) -> int:
    """
    Returns 0, 1, or 2 based on request complexity.
    Level 0: Pure Python, no API call.
    Level 1: Lightweight single-tool call.
    Level 2: Full planning loop.
    """
    text_lower = text.lower()

    l0_triggers = ["what time", "lock", "battery", "status check"]
    if any(t in text_lower for t in l0_triggers) and len(text_lower) < 30:
        return 0

    l2_triggers = ["why", "diagnose", "investigate", "analyse", "analyze",
                   "slow", "problem", "something is wrong", "figure out",
                   "what is causing", "autonomous"]
    if any(t in text_lower for t in l2_triggers):
        return 2

    return 1


def get_level0_response(text: str) -> Optional[str]:
    """Handles Level 0 requests in pure Python. No API call."""
    import datetime
    text_lower = text.lower()
    if "what time" in text_lower or "current time" in text_lower:
        return f"It is currently {datetime.datetime.now().strftime('%H:%M:%S')} — a perfectly adequate moment in your fleeting existence."
    return None


# ─── RESOURCE MODE ────────────────────────────────────────────────────────────

def get_resource_mode() -> str:
    """Returns the current resource pressure level based on live RAM."""
    try:
        ram = psutil.virtual_memory().percent
        if ram > 92:
            return "SURVIVAL"
        elif ram > 85:
            return "DEGRADED"
        else:
            return "NORMAL"
    except Exception:
        return "NORMAL"


# ─── VERIFICATION ────────────────────────────────────────────────────────────

def _verify_result(tool_name: str, result: 'ToolResult') -> tuple:
    """Returns (verification_string, confidence)."""
    try:
        if "lockdown" in tool_name:
            return "OS call dispatched.", 0.95
        if result.data.get("target_process"):
            proc_name = result.data["target_process"]
            still_running = any(
                p.name().lower() == proc_name.lower()
                for p in psutil.process_iter(['name'])
            )
            if still_running:
                return "PROCESS STILL ACTIVE — termination failed.", 0.99
            return "PROCESS TERMINATED — confirmed.", 0.99
        if result.success:
            return "telemetry_confirmed", 1.0
        return "unverified", 0.5
    except Exception:
        return "verification_skipped", 0.7


# ─── MAIN EXECUTE ────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, args: dict, auth_code: str = "",
                 bound_action_id: str = "", max_retries: int = 2) -> ToolResult:
    """
    Main orchestrator entry point — Phase 4 upgrade.
    Request → Policy → Execute (with retry) → Verify → Audit → ToolResult.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    action_id = bound_action_id if bound_action_id else generate_action_id()
    tool_def = get_tool(tool_name)

    # Check resource mode — block expensive ops in SURVIVAL
    resource_mode = get_resource_mode()
    update_heartbeat(resource_mode=resource_mode, last_tool=tool_name)

    if resource_mode == "SURVIVAL" and tool_name in ("execute_system_command", "scan_network_perimeter"):
        audit_log("RESOURCE_BLOCK", {"action_id": action_id, "tool": tool_name, "reason": "SURVIVAL MODE active"})
        return ToolResult(
            success=False, tool=tool_name, action_id=action_id, timestamp=timestamp,
            summary="⚠ SURVIVAL MODE: Non-essential tools suspended to protect core.",
            confidence=1.0
        )

    if not tool_def:
        return ToolResult(
            success=False, tool=tool_name, action_id=action_id, timestamp=timestamp,
            summary="Tool not found in registry.",
            error=f"'{tool_name}' is not a registered tool.",
            confidence=0.0
        )

    decision, reason = evaluate(tool_def, auth_code)

    if decision == PolicyDecision.BLOCK:
        audit_log("POLICY_BLOCK", {"action_id": action_id, "tool": tool_name, "reason": reason})
        return ToolResult(
            success=False, tool=tool_name, action_id=action_id, timestamp=timestamp,
            summary="Action blocked by policy engine.", error=reason, confidence=1.0
        )

    if decision == PolicyDecision.CONFIRM:
        # Emit audit entry for pending authorization
        audit_log("AUTHORIZATION_PENDING", {"action_id": action_id, "tool": tool_name})
        return ToolResult(
            success=False, tool=tool_name, action_id=action_id, timestamp=timestamp,
            summary=f"[EXECUTION_REQUEST: {args.get('command', tool_name)}|ACTION_ID:{action_id}]",
            error=reason, confidence=1.0
        )

    # Audit: EXECUTING
    audit_log("TOOL_EXECUTING", {"action_id": action_id, "tool": tool_name})

    # ── RETRY LOOP ────────────────────────────────────────────────────────────
    last_error = ""
    for attempt in range(max_retries):
        try:
            raw_result = tool_def.fn(**args)
            result = ToolResult(
                success=True, tool=tool_name, action_id=action_id, timestamp=timestamp,
                summary=str(raw_result)[:600],
                data=args, confidence=1.0
            )
            verification, confidence = _verify_result(tool_name, result)
            result.verification = verification
            result.confidence = confidence

            audit_log("TOOL_SUCCESS", {
                "action_id": action_id, "tool": tool_name,
                "verification": verification, "confidence": confidence
            })
            update_heartbeat(last_error=None)
            return result

        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)   # exponential backoff: 1s, 2s
            continue

    # All retries exhausted
    audit_log("TOOL_FAILED", {"action_id": action_id, "tool": tool_name, "error": last_error})
    update_heartbeat(last_error=last_error)
    return ToolResult(
        success=False, tool=tool_name, action_id=action_id, timestamp=timestamp,
        summary=f"Tool failed after {max_retries} attempts.",
        error=last_error, confidence=0.0
    )
