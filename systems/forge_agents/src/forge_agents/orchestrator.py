"""Multi-agent orchestrator with explicit budgets and stop conditions."""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .agents import BaseAgent, Coder, Critic, Planner, Researcher
from .memory import Scratchpad, Transcript
from .providers import LLMProvider
from .tools import ToolRegistry, default_registry
from .types import AgentStep, Message, RunResult


class StopReason(str, Enum):
    APPROVED = "approved"
    MAX_STEPS = "max_steps"
    MAX_SECONDS = "max_seconds"
    NO_PROGRESS = "no_progress"
    ERROR = "error"


@dataclass
class RunBudget:
    """Hard limits for a single orchestrator run."""
    max_steps: int = 12
    max_seconds: float = 60.0
    max_revisions: int = 3


class Orchestrator:
    """Runs a planner → researcher → coder → critic loop until approved or budget exhausted."""

    def __init__(
        self,
        provider: LLMProvider,
        tools: Optional[ToolRegistry] = None,
        agents: Optional[List[BaseAgent]] = None,
        budget: Optional[RunBudget] = None,
    ) -> None:
        self.provider = provider
        self.tools = tools if tools is not None else default_registry()
        self.budget = budget or RunBudget()
        self.agents: List[BaseAgent] = agents or [
            Planner(provider),
            Researcher(provider, tools=self.tools),
            Coder(provider),
            Critic(provider),
        ]

    def run(self, task: str) -> RunResult:
        transcript = Transcript()
        scratchpad = Scratchpad()
        transcript.add(Message(role="user", content=task))

        steps: List[AgentStep] = []
        start = time.monotonic()
        stop_reason = StopReason.MAX_STEPS
        revisions = 0
        last_answer = ""

        agents_by_name = {a.name: a for a in self.agents}

        # Ordered pipeline; the loop restarts at coder when critic asks for revision.
        pipeline = ["planner", "researcher", "coder", "critic"]
        idx = 0

        while len(steps) < self.budget.max_steps:
            if time.monotonic() - start > self.budget.max_seconds:
                stop_reason = StopReason.MAX_SECONDS
                break

            name = pipeline[idx]
            agent = agents_by_name.get(name)
            if agent is None:
                stop_reason = StopReason.ERROR
                break

            try:
                step = agent.step(transcript, scratchpad, task)
            except Exception as exc:  # noqa: BLE001
                transcript.add(Message(
                    role="system",
                    content=f"Agent {name} raised: {type(exc).__name__}: {exc}",
                ))
                stop_reason = StopReason.ERROR
                break

            steps.append(step)
            # Persist selected outputs to scratchpad for downstream agents.
            answer = _agent_answer(transcript, name)
            if answer:
                scratchpad.set(f"{name}_answer", answer)
                if name == "coder":
                    last_answer = answer

            if name == "critic":
                verdict = (answer or "").strip().upper()
                if verdict.startswith("APPROVED"):
                    stop_reason = StopReason.APPROVED
                    break
                revisions += 1
                if revisions > self.budget.max_revisions:
                    stop_reason = StopReason.NO_PROGRESS
                    break
                # Loop back to coder for another attempt.
                idx = pipeline.index("coder")
                continue

            idx = (idx + 1) % len(pipeline)

        elapsed = time.monotonic() - start
        final_answer = last_answer or _agent_answer(transcript, "coder") or ""
        return RunResult(
            task=task,
            final_answer=final_answer,
            steps=steps,
            transcript=transcript.all(),
            stop_reason=stop_reason.value,
            step_count=len(steps),
            elapsed_seconds=round(elapsed, 4),
        )


def _agent_answer(transcript: Transcript, agent_name: str) -> str:
    """Return the most recent message content emitted by the given agent."""
    for msg in reversed(transcript.all()):
        if msg.role == "agent" and msg.name == agent_name:
            return msg.content
    return ""
