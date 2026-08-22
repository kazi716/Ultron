"""
ULTRON PLANNER — Phase 3 Cognitive Architecture
Gemini creates the plan. The Orchestrator owns execution.
They never mix.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class GoalStatus(Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    REPLANNING = "REPLANNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class PlanStep:
    tool: str
    reason: str
    status: str = "PENDING"   # PENDING | EXECUTING | DONE | SKIPPED
    observation: str = ""     # what actually happened


@dataclass
class Goal:
    objective: str
    steps: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    status: GoalStatus = GoalStatus.PENDING
    current_step: int = 0
    observations: list = field(default_factory=list)
    final_result: str = ""
    confidence: float = 1.0

    def to_hud_str(self) -> str:
        lines = [
            f"GOAL #{self.id}",
            f"OBJECTIVE: {self.objective}",
            f"STATUS: {self.status.value}",
            f"CONFIDENCE: {int(self.confidence * 100)}%",
            "PLAN:"
        ]
        icons = {"PENDING": "○", "EXECUTING": "→", "DONE": "✓", "SKIPPED": "↷"}
        for i, step in enumerate(self.steps):
            icon = icons.get(step.status, "○")
            lines.append(f"  [{icon}] {step.tool} — {step.reason}")
        return "\n".join(lines)


# --- Active goal registry (lightweight in-memory) ---
_active_goal: Optional[Goal] = None


def set_active_goal(goal: Goal):
    global _active_goal
    _active_goal = goal
    from core.state import save_checkpoint, audit_log
    audit_log("GOAL_CREATED", {"goal_id": goal.id, "objective": goal.objective})
    save_checkpoint(goal)


def get_active_goal() -> Optional[Goal]:
    return _active_goal


def clear_active_goal():
    global _active_goal
    if _active_goal:
        _active_goal.status = GoalStatus.COMPLETE
        from core.state import save_checkpoint, audit_log, clear_checkpoint
        audit_log("GOAL_COMPLETE", {"goal_id": _active_goal.id, "objective": _active_goal.objective})
        clear_checkpoint()
    _active_goal = None


def parse_plan_from_gemini(raw_text: str) -> Optional[Goal]:
    """
    Tries to parse a JSON plan from Gemini's response.
    Returns a Goal object if found, None otherwise.
    """
    try:
        # Look for a JSON block inside the text
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start == -1 or end == 0:
            return None

        json_str = raw_text[start:end]
        data = json.loads(json_str)

        if "goal" not in data or "steps" not in data:
            return None

        steps = [
            PlanStep(tool=s.get("tool", ""), reason=s.get("reason", ""))
            for s in data["steps"]
        ]

        return Goal(objective=data["goal"], steps=steps)
    except Exception:
        return None
