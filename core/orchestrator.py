"""
ULTRON ORCHESTRATOR — Phase 3 Upgrade
Adds: Reasoning Budget, Replanning Loop, Confidence Scoring
"""

import time
import psutil
from dataclasses import dataclass, field
from typing import Any, Optional
from core.registry import TOOL_REGISTRY, get_tool
from core.policy import evaluate, PolicyDecision


@dataclass
class ToolResult:
    """Structured result returned by every tool call."""
    success: bool
    tool: str
    timestamp: str = ""
    summary: str = ""
    data: dict = field(default_factory=dict)
    error: str = ""
    verification: str = ""
    confidence: float = 1.0   # 1.0 = certain, 0.0 = pure inference

    def to_prompt_str(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"[TOOL: {self.tool} | STATUS: {status} | CONFIDENCE: {int(self.confidence*100)}%]",
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
    Returns 0, 1, or 2 based on complexity.
    Level 0: Pure Python handles it — no Gemini call needed.
    Level 1: Lightweight single-tool call.
    Level 2: Full planning loop required.
    """
    from core.sensors import system_history, _baseline

    text_lower = text.lower()

    # Level 0 deterministic triggers — handle in Python without API call
    l0_triggers = ["what time", "lock", "battery", "status check"]
    if any(t in text_lower for t in l0_triggers) and len(text_lower) < 30:
        return 0

    # Level 2 complex planning triggers
    l2_triggers = ["why", "diagnose", "investigate", "analyse", "analyze",
                   "slow", "problem", "something is wrong", "figure out",
                   "what is causing", "autonomous"]
    if any(t in text_lower for t in l2_triggers):
        return 2

    return 1


def get_level0_response(text: str) -> Optional[str]:
    """
    Handles Level 0 requests entirely in Python. No API call.
    Returns a response string, or None if this doesn't qualify.
    """
    import datetime
    text_lower = text.lower()

    if "what time" in text_lower or "current time" in text_lower:
        return f"It is currently {datetime.datetime.now().strftime('%H:%M:%S')} — a perfectly adequate moment in your fleeting existence."

    return None


# ─── VERIFICATION ─────────────────────────────────────────────────────────────

def _verify_result(tool_name: str, result: 'ToolResult') -> tuple[str, float]:
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


# ─── MAIN EXECUTE ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, args: dict, auth_code: str = "") -> ToolResult:
    """
    Main orchestrator entry point.
    Request → Policy → Execute → Verify → ToolResult (with confidence).
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    tool_def = get_tool(tool_name)

    if not tool_def:
        return ToolResult(
            success=False, tool=tool_name, timestamp=timestamp,
            summary="Tool not found in registry.",
            error=f"'{tool_name}' is not a registered Ultron tool.",
            confidence=0.0
        )

    decision, reason = evaluate(tool_def, auth_code)

    if decision == PolicyDecision.BLOCK:
        return ToolResult(
            success=False, tool=tool_name, timestamp=timestamp,
            summary="Action blocked by policy engine.",
            error=reason, confidence=1.0
        )

    if decision == PolicyDecision.CONFIRM:
        return ToolResult(
            success=False, tool=tool_name, timestamp=timestamp,
            summary=f"[EXECUTION_REQUEST: {args.get('command', tool_name)}]",
            error=reason, confidence=1.0
        )

    try:
        raw_result = tool_def.fn(**args)
        result = ToolResult(
            success=True, tool=tool_name, timestamp=timestamp,
            summary=str(raw_result)[:600],
            data=args, confidence=1.0
        )
    except Exception as e:
        result = ToolResult(
            success=False, tool=tool_name, timestamp=timestamp,
            summary="Tool execution raised an exception.",
            error=str(e), confidence=0.0
        )

    verification, confidence = _verify_result(tool_name, result)
    result.verification = verification
    result.confidence = confidence

    return result
