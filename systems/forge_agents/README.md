# forge_agents

A dependency-light multi-agent orchestrator for building AI workflows.

**Independent of** the FORGE v3 cognitive-economic modules at the repo root. This
package lives entirely under `systems/forge_agents/` and can be extracted to its
own repository without modification.

## What it is

A small, honest, well-tested orchestrator for **planner → researcher → coder → critic**
style loops with:

- Pluggable **LLM provider** interface (works offline via `EchoProvider`; adapters for
  OpenAI/Anthropic can be added without touching the core).
- Typed **agent** base class with structured messages.
- **Tool registry** with safe built-ins: file reading, arithmetic eval, HTTP fetch (opt-in).
- **Memory** (in-process transcript + key-value scratchpad).
- **Orchestrator loop** with step budget, wall-clock budget, and stop conditions.
- **CLI**: `python -m forge_agents.cli run "your task"`
- **REST API** (optional, requires `fastapi` + `uvicorn`): `POST /run`, `GET /health`.

## What it is not

- Not "enterprise-ready". No auth, no billing, no multi-tenancy, no SLA.
- Not a replacement for LangChain / LlamaIndex / CrewAI. It's ~1k lines you can read.
- Not a source of business value on its own — it's a foundation you build on.

## Install (dev)

```bash
cd systems/forge_agents
python -m pip install -e ".[dev]"
pytest
```

Zero required runtime dependencies. `fastapi`/`uvicorn` are optional extras used only by
the REST server. `httpx` is an optional extra used only by the HTTP-fetch tool.

## Quick start

```python
from forge_agents import Orchestrator, EchoProvider

orch = Orchestrator(provider=EchoProvider())
result = orch.run("Summarize the file README.md")
print(result.final_answer)
print(result.transcript)
```

## PS2-style runtime view (running agents)

Render a PlayStation-2-inspired HUD for agent execution:

```bash
python -m forge_agents.cli run "Draft launch checklist" --ps2-view
python -m forge_agents.cli run "Draft launch checklist" --ps2-view --ps2-replay
```

## Layout

```
systems/forge_agents/
├── pyproject.toml
├── README.md
├── src/forge_agents/
│   ├── __init__.py
│   ├── types.py            # dataclasses: Message, ToolCall, RunResult, ...
│   ├── memory.py           # Transcript + Scratchpad
│   ├── providers.py        # LLMProvider protocol + EchoProvider
│   ├── tools.py            # Tool registry + safe built-ins
│   ├── agents.py           # BaseAgent, Planner, Researcher, Coder, Critic
│   ├── orchestrator.py     # Multi-agent loop with budgets & stop conditions
│   ├── cli.py              # `python -m forge_agents.cli`
│   └── server.py           # Optional FastAPI app
└── tests/
    ├── test_memory.py
    ├── test_tools.py
    ├── test_agents.py
    └── test_orchestrator.py
```
