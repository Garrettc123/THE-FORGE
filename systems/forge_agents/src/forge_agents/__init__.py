"""forge_agents: dependency-light multi-agent orchestrator."""
from .types import Message, ToolCall, ToolResult, RunResult, AgentStep
from .memory import Transcript, Scratchpad
from .providers import LLMProvider, EchoProvider, ProviderError
from .tools import Tool, ToolRegistry, default_registry
from .agents import BaseAgent, Planner, Researcher, Coder, Critic
from .orchestrator import Orchestrator, RunBudget, StopReason

__all__ = [
    "Message",
    "ToolCall",
    "ToolResult",
    "RunResult",
    "AgentStep",
    "Transcript",
    "Scratchpad",
    "LLMProvider",
    "EchoProvider",
    "ProviderError",
    "Tool",
    "ToolRegistry",
    "default_registry",
    "BaseAgent",
    "Planner",
    "Researcher",
    "Coder",
    "Critic",
    "Orchestrator",
    "RunBudget",
    "StopReason",
]

__version__ = "0.1.0"
