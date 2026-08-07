"""Optional FastAPI server.

Requires the `server` extra: `pip install forge-agents[server]`.
Import is guarded so the core package remains dependency-free.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

try:
    from fastapi import FastAPI, HTTPException  # type: ignore
    from pydantic import BaseModel  # type: ignore
except ImportError as exc:  # pragma: no cover - depends on optional extra
    raise RuntimeError(
        "server module requires the 'server' extra: pip install forge-agents[server]"
    ) from exc

from .orchestrator import Orchestrator, RunBudget
from .providers import EchoProvider
from .tools import default_registry


class RunRequest(BaseModel):  # type: ignore[misc]
    task: str
    max_steps: int = 12
    max_seconds: float = 60.0
    max_revisions: int = 3
    enable_http: bool = False


def create_app(orchestrator_factory: Optional[Any] = None) -> "FastAPI":
    app = FastAPI(title="forge-agents", version="0.1.0")

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/run")
    def run(req: RunRequest) -> Dict[str, Any]:
        if not req.task.strip():
            raise HTTPException(status_code=400, detail="task must be non-empty")
        if orchestrator_factory is not None:
            orch = orchestrator_factory()
        else:
            orch = Orchestrator(
                provider=EchoProvider(),
                tools=default_registry(enable_http=req.enable_http),
                budget=RunBudget(
                    max_steps=req.max_steps,
                    max_seconds=req.max_seconds,
                    max_revisions=req.max_revisions,
                ),
            )
        result = orch.run(req.task)
        return asdict(result)

    return app


app = None  # created lazily by callers who want to serve
