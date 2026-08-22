"""
ULTRON POLICY ENGINE
Enforces risk-based access control for every tool call.
Policy is determined by the tool's metadata, NOT by scanning command strings.
"""

import os
from core.registry import RiskLevel, ToolDefinition


class PolicyDecision:
    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"
    BLOCK = "BLOCK"


def evaluate(tool: ToolDefinition, auth_code: str = "") -> tuple[str, str]:
    """
    Evaluates whether a tool call is allowed.
    Returns a tuple of (decision, reason).
    """
    correct_password = os.getenv("ULTRON_PASSWORD", "ironman")
    risk = tool.risk

    # SAFE and LOW tools always auto-execute
    if risk in (RiskLevel.SAFE, RiskLevel.LOW):
        return PolicyDecision.ALLOW, "Auto-approved: low-risk operation."

    # CRITICAL tools are always blocked unless the correct auth is supplied
    if risk == RiskLevel.CRITICAL:
        if auth_code == correct_password:
            return PolicyDecision.ALLOW, "Authorized: CRITICAL action approved by user."
        return PolicyDecision.CONFIRM, f"CRITICAL action requires authorization. Trigger UI card: EXECUTION_REQUEST"

    # MODERATE and HIGH tools require confirmation
    if risk in (RiskLevel.MODERATE, RiskLevel.HIGH):
        if auth_code == correct_password:
            return PolicyDecision.ALLOW, f"Authorized: {risk.value} action approved by user."
        return PolicyDecision.CONFIRM, f"{risk.value} action requires confirmation. Trigger UI card: EXECUTION_REQUEST"

    return PolicyDecision.BLOCK, "Unknown risk level. Blocked by default."
