"""LLM provider abstraction.

The core does not depend on any specific LLM SDK. Implement `LLMProvider.complete`
to add OpenAI, Anthropic, local models, etc.

`EchoProvider` is a deterministic offline provider used for tests and CLI dry-runs.
It also demonstrates the structured protocol the agents expect.
"""
from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from .types import Message


class ProviderError(RuntimeError):
    """Raised when a provider fails to produce a completion."""


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface an LLM provider must implement.

    Implementations should be side-effect free apart from the network call itself.
    """

    def complete(self, messages: List[Message], *, agent: str) -> str:
        """Return the assistant text for the given transcript slice."""
        ...


class EchoProvider:
    """Deterministic offline provider.

    For each agent it returns a stable, structured string so that agents and
    the orchestrator can be tested without any network access.

    The output format is intentionally simple and machine-parseable:

        THOUGHT: <one line>
        TOOL: <tool_name> {"arg": "value"}      # optional
        ANSWER: <text>                          # only when done

    Agents parse whichever lines they need.
    """

    def __init__(self, script: dict | None = None) -> None:
        # Optional per-agent override: {"planner": ["step1", "step2"], ...}
        self._script = script or {}
        self._counters: dict[str, int] = {}

    def complete(self, messages: List[Message], *, agent: str) -> str:
        if agent in self._script:
            idx = self._counters.get(agent, 0)
            responses = self._script[agent]
            if idx < len(responses):
                self._counters[agent] = idx + 1
                return responses[idx]

        last_user = next(
            (m.content for m in reversed(messages) if m.role in ("user", "agent")),
            "",
        )
        short = last_user.strip().splitlines()[0][:200] if last_user else ""

        if agent == "planner":
            return (
                "THOUGHT: Break the task into research, implementation, and review.\n"
                "ANSWER: 1) research context 2) draft solution 3) critique 4) finalize"
            )
        if agent == "researcher":
            return (
                f"THOUGHT: Gather any relevant context for: {short}\n"
                "ANSWER: No external sources consulted (offline echo provider)."
            )
        if agent == "coder":
            return (
                f"THOUGHT: Draft a direct response to: {short}\n"
                f"ANSWER: {short or 'Task acknowledged.'}"
            )
        if agent == "critic":
            return (
                "THOUGHT: Check the draft for correctness and completeness.\n"
                "ANSWER: APPROVED"
            )
        return f"THOUGHT: (echo)\nANSWER: {short}"
