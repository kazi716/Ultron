"""
ULTRON TOOL REGISTRY
Every tool is defined with structured metadata.
Policy is attached to the TOOL, not inferred from command strings.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class RiskLevel(Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolCategory(Enum):
    READ = "READ"
    ACTION = "ACTION"
    SYSTEM = "SYSTEM"
    VISION = "VISION"
    WRITE = "WRITE"
    NETWORK = "NETWORK"


@dataclass
class ToolDefinition:
    name: str
    fn: Callable
    description: str
    category: ToolCategory
    risk: RiskLevel
    requires_confirmation: bool
    timeout: int = 15  # seconds
    verification_method: Optional[str] = None  # how to verify the result


# --- TOOL REGISTRY ---
# Populated by register_tools() called from tools.py after functions are defined.
TOOL_REGISTRY: dict[str, ToolDefinition] = {}


def register(
    name: str,
    description: str,
    category: ToolCategory,
    risk: RiskLevel,
    requires_confirmation: bool = False,
    timeout: int = 15,
    verification_method: Optional[str] = None
):
    """Decorator to register a function into the Tool Registry with metadata."""
    def decorator(fn: Callable) -> Callable:
        TOOL_REGISTRY[name] = ToolDefinition(
            name=name,
            fn=fn,
            description=description,
            category=category,
            risk=risk,
            requires_confirmation=requires_confirmation,
            timeout=timeout,
            verification_method=verification_method
        )
        return fn  # Return the ORIGINAL function for schema generation only
    return decorator


def get_tool(name: str) -> Optional[ToolDefinition]:
    return TOOL_REGISTRY.get(name)


def list_tools() -> str:
    """Returns a human-readable summary of all registered tools."""
    lines = ["--- ULTRON TOOL REGISTRY ---"]
    for name, defn in TOOL_REGISTRY.items():
        confirm = "YES" if defn.requires_confirmation else "AUTO"
        lines.append(f"[{defn.risk.value:<8}] [{confirm:<4}] {name} ({defn.category.value})")
    return "\n".join(lines)
