"""Core dataclasses shared across the package."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """A single message in a transcript."""
    role: str          # "system" | "user" | "assistant" | "tool" | "agent"
    content: str
    name: Optional[str] = None   # agent name or tool name
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """A structured request from an agent to invoke a tool."""
    tool: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Structured result returned from a tool call."""
    tool: str
    ok: bool
    output: Any = None
    error: Optional[str] = None


@dataclass
class AgentStep:
    """One agent's turn: what they said, what they called, what came back."""
    agent: str
    thought: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None


@dataclass
class RunResult:
    """Final result of an Orchestrator.run() invocation."""
    task: str
    final_answer: str
    steps: List[AgentStep] = field(default_factory=list)
    transcript: List[Message] = field(default_factory=list)
    stop_reason: str = "completed"
    step_count: int = 0
    elapsed_seconds: float = 0.0
