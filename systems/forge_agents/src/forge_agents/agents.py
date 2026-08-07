"""Agent implementations.

Every agent is a `BaseAgent` subclass with:
- a name and a system prompt,
- a `step(...)` method that takes the shared transcript + scratchpad and returns
  an `AgentStep`.

Agents parse the provider's structured text output (THOUGHT / TOOL / ANSWER lines).
Free-form provider responses without those markers are still handled gracefully:
the full text becomes the "answer" and no tool call is emitted.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from .memory import Scratchpad, Transcript
from .providers import LLMProvider
from .tools import ToolRegistry
from .types import AgentStep, Message, ToolCall, ToolResult

_TOOL_RE = re.compile(r"^\s*TOOL:\s*(?P<name>[a-zA-Z_][\w-]*)\s*(?P<args>\{.*\})?\s*$")


def _parse_response(text: str) -> tuple[str, Optional[ToolCall], str]:
    """Parse a provider response into (thought, optional tool_call, answer_text)."""
    thought_parts: list[str] = []
    answer_parts: list[str] = []
    tool_call: Optional[ToolCall] = None
    mode: Optional[str] = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.upper().startswith("THOUGHT:"):
            mode = "thought"
            payload = stripped[len("THOUGHT:"):].strip()
            if payload:
                thought_parts.append(payload)
            continue
        if stripped.upper().startswith("ANSWER:"):
            mode = "answer"
            payload = stripped[len("ANSWER:"):].strip()
            if payload:
                answer_parts.append(payload)
            continue
        m = _TOOL_RE.match(line)
        if m:
            args: dict = {}
            if m.group("args"):
                try:
                    args = json.loads(m.group("args"))
                except json.JSONDecodeError:
                    args = {"_raw": m.group("args")}
            tool_call = ToolCall(tool=m.group("name"), args=args)
            mode = None
            continue
        if mode == "thought":
            thought_parts.append(line)
        elif mode == "answer":
            answer_parts.append(line)
        else:
            # Free-form text before any marker is treated as the answer.
            answer_parts.append(line)

    thought = "\n".join(thought_parts).strip()
    answer = "\n".join(answer_parts).strip()
    return thought, tool_call, answer


class BaseAgent:
    """Base class: name, system prompt, and one `step()` per turn."""

    name: str = "agent"
    system_prompt: str = "You are a helpful agent."

    def __init__(
        self,
        provider: LLMProvider,
        tools: Optional[ToolRegistry] = None,
    ) -> None:
        self.provider = provider
        self.tools = tools

    def _build_messages(
        self,
        transcript: Transcript,
        scratchpad: Scratchpad,
        task: str,
    ) -> list[Message]:
        messages: list[Message] = [
            Message(role="system", content=self.system_prompt, name=self.name),
            Message(role="user", content=f"TASK: {task}"),
        ]
        scratch = scratchpad.snapshot()
        if scratch:
            messages.append(Message(
                role="system",
                content="SCRATCHPAD:\n" + json.dumps(scratch, indent=2, default=str),
                name=self.name,
            ))
        # Include the tail of the transcript for context (bounded).
        messages.extend(transcript.last(20))
        return messages

    def step(
        self,
        transcript: Transcript,
        scratchpad: Scratchpad,
        task: str,
    ) -> AgentStep:
        messages = self._build_messages(transcript, scratchpad, task)
        response = self.provider.complete(messages, agent=self.name)
        thought, tool_call, answer = _parse_response(response)

        tool_result: Optional[ToolResult] = None
        if tool_call and self.tools is not None:
            tool = self.tools.get(tool_call.tool)
            if tool is None:
                tool_result = ToolResult(
                    tool=tool_call.tool,
                    ok=False,
                    error=f"Unknown tool: {tool_call.tool}",
                )
            else:
                tool_result = tool.call(**tool_call.args)

        # Record what this agent said (and what came back).
        transcript.add(Message(role="agent", content=answer or thought, name=self.name))
        if tool_result is not None:
            transcript.add(Message(
                role="tool",
                content=(str(tool_result.output) if tool_result.ok else (tool_result.error or "")),
                name=tool_result.tool,
                meta={"ok": tool_result.ok},
            ))

        return AgentStep(
            agent=self.name,
            thought=thought,
            tool_call=tool_call,
            tool_result=tool_result,
        )


class Planner(BaseAgent):
    name = "planner"
    system_prompt = (
        "You are the planner. Decompose the user's task into concrete, ordered steps. "
        "Reply in the structured format: THOUGHT: <reasoning>\\nANSWER: <numbered plan>."
    )


class Researcher(BaseAgent):
    name = "researcher"
    system_prompt = (
        "You are the researcher. Gather facts needed to complete the plan. "
        "You may call tools via a line like: TOOL: <name> {\"arg\": \"value\"}. "
        "Then reply: THOUGHT: <reasoning>\\nANSWER: <findings>."
    )


class Coder(BaseAgent):
    name = "coder"
    system_prompt = (
        "You are the coder / doer. Produce the concrete artifact that answers the task "
        "using the plan and research so far. Reply: THOUGHT: <reasoning>\\nANSWER: <artifact>."
    )


class Critic(BaseAgent):
    name = "critic"
    system_prompt = (
        "You are the critic. Review the coder's answer for correctness, completeness, "
        "and safety. Reply: THOUGHT: <reasoning>\\nANSWER: APPROVED  — or —  "
        "ANSWER: REVISE: <what to change>."
    )
