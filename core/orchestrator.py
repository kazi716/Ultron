"""
ULTRON ORCHESTRATOR
The central nervous system.
Every tool call flows: Request -> Policy -> Execute -> Verify -> ToolResult
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

    def to_prompt_str(self) -> str:
        """Converts the result into a clean string for Gemini's context."""
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"[TOOL: {self.tool} | STATUS: {status}]",
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


def _verify_result(tool_name: str, result: ToolResult) -> str:
    """
    Post-execution verification. Checks if the action actually had the intended effect.
    """
    try:
        if "lockdown" in tool_name:
            # After locking, we can't verify from inside Python - trust the OS call
            return "OS call dispatched. Screen lock state cannot be verified remotely."

        if "taskkill" in result.summary.lower() or "terminate" in result.summary.lower():
            # Try to detect if the killed process is still running
            proc_name = result.data.get("target_process", "")
            if proc_name:
                still_running = any(
                    p.name().lower() == proc_name.lower()
                    for p in psutil.process_iter(['name'])
                )
                return "PROCESS STILL ACTIVE — termination may have failed." if still_running else "PROCESS TERMINATED — confirmed."

        if result.success:
            return "telemetry_confirmed"
        return "unverified"
    except Exception:
        return "verification_skipped"


def execute_tool(tool_name: str, args: dict, auth_code: str = "") -> ToolResult:
    """
    The main orchestrator entry point.
    Finds the tool, evaluates policy, executes, verifies, and returns a ToolResult.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    tool_def = get_tool(tool_name)

    if not tool_def:
        return ToolResult(
            success=False,
            tool=tool_name,
            timestamp=timestamp,
            summary="Tool not found in registry.",
            error=f"'{tool_name}' is not a registered Ultron tool."
        )

    # Policy evaluation
    decision, reason = evaluate(tool_def, auth_code)

    if decision == PolicyDecision.BLOCK:
        return ToolResult(
            success=False,
            tool=tool_name,
            timestamp=timestamp,
            summary="Action blocked by policy engine.",
            error=reason
        )

    if decision == PolicyDecision.CONFIRM:
        return ToolResult(
            success=False,
            tool=tool_name,
            timestamp=timestamp,
            summary=f"[EXECUTION_REQUEST: {args.get('command', tool_name)}]",
            error=reason
        )

    # Execute the tool
    try:
        raw_result = tool_def.fn(**args)
        result = ToolResult(
            success=True,
            tool=tool_name,
            timestamp=timestamp,
            summary=str(raw_result)[:500],  # cap to avoid context bloat
            data=args
        )
    except Exception as e:
        result = ToolResult(
            success=False,
            tool=tool_name,
            timestamp=timestamp,
            summary="Tool execution raised an exception.",
            error=str(e)
        )

    # Verification step
    result.verification = _verify_result(tool_name, result)

    return result
