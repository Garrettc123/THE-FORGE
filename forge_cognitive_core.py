#!/usr/bin/env python3
"""
forge_cognitive_core.py — INERT STUB
====================================

This file is a deliberately inert placeholder for the real
``forge_cognitive_core`` module. It exists solely so that:

  * ``expand_core.py`` short-circuits (file already present, > 1000 bytes)
  * ``from forge_cognitive_core import Forge`` succeeds
  * ``python forge_all.py bridge`` / ``status`` / ``tower`` complete without
    raising, letting the "FORGE Cognitive Control / forge" GitHub Actions
    check turn green.

It performs NO work:
  * no network calls
  * no capital movement
  * no external side effects (only writes the local JSON snapshot files
    that ``forge_all.py`` already expects to upload as workflow artifacts)

All methods return static, empty, or trivially-safe structures. This module
does NOT reconstruct, guess at, or approximate the behavior of the original
compressed ``forge_cognitive_core.py.zlib.b64.part*`` blob. Replace this file
with the real source when it becomes available.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

__all__ = [
    "PROTOCOL",
    "FORGE_VERSION",
    "asdict",
    "utc_iso",
    "StateVector",
    "ReplicationGate",
    "Forge",
]

PROTOCOL = "FORGE v3 (stub)"
FORGE_VERSION = "0.0.0-stub"


def utc_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StateVector:
    """Minimal state container matching the fields used by the bridge."""
    cash: float = 0.0
    mrr: float = 0.0
    revenue: float = 0.0
    profit: float = 0.0
    customers: int = 0
    churn: float = 0.0
    cac: float = 0.0
    assets: float = 0.0
    risk_score: float = 0.0
    capacity: float = 0.0
    infrastructure: float = 0.0
    productivity: float = 0.0


@dataclass
class ReplicationGate:
    open: bool = False
    reason: str = "stub: replication disabled"


@dataclass
class _StubAgent:
    name: str

    def report(self) -> Dict[str, Any]:
        return {"agent": self.name, "status": "stub", "notes": "inert placeholder"}


class Forge:
    """
    Inert stub of the Forge cognitive-cycle orchestrator.

    Exposes the attribute and method surface consumed by ``forge_all.py``
    and ``forge_garcar_bridge.py`` and nothing more.
    """

    def __init__(self) -> None:
        self.cycle_count: int = 0
        self.sentinel = _StubAgent("sentinel")
        self.delta = _StubAgent("delta")
        self.treasury = _StubAgent("treasury")
        self.alpha = _StubAgent("alpha")
        self.beta = _StubAgent("beta")
        self.gamma = _StubAgent("gamma")
        self.knowledge = _StubAgent("knowledge")
        self.executive = _StubAgent("executive")
        self.replication_gate = ReplicationGate()
        self._state: Optional[StateVector] = None

    # --- Core lifecycle ---------------------------------------------------

    def run_cycle(
        self,
        external_signals: Optional[Iterable[Dict[str, Any]]] = None,
        initial_state: Optional[StateVector] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        self.cycle_count += 1
        if initial_state is not None:
            self._state = initial_state

        signal_list = list(external_signals or [])

        return {
            "cycle": self.cycle_count,
            "timestamp": utc_iso(),
            "mode": "dry-run" if dry_run else "live",
            "event_count": 0,
            "priority_queue": [],
            "external_signals_received": len(signal_list),
            "horizon_scorecards": [],
            "phases": {
                "learning": {
                    "causal_updates": [],
                    "open_experiments": 0,
                    "closed_experiments": 0,
                },
                "outcome": {},
            },
            "control_tower": (
                "[FORGE STUB] Inert core loaded. No cognitive work performed. "
                "Replace forge_cognitive_core.py with the real module."
            ),
            "protocol": PROTOCOL,
            "forge_version": FORGE_VERSION,
        }

    def demo_scenario(self, live: bool = False) -> Dict[str, Any]:
        return self.run_cycle(dry_run=not live)

    # --- State persistence ------------------------------------------------

    def dump_state(self, path: Path) -> Path:
        path = Path(path)
        snapshot = {
            "cycle_count": self.cycle_count,
            "state": asdict(self._state) if self._state is not None else None,
            "replication_gate": asdict(self.replication_gate),
            "timestamp": utc_iso(),
            "protocol": PROTOCOL,
            "forge_version": FORGE_VERSION,
            "note": "inert stub snapshot",
        }
        path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        return path

    def load_state(self, path: Path) -> bool:
        path = Path(path)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        self.cycle_count = int(data.get("cycle_count", 0))
        state_dict = data.get("state")
        if isinstance(state_dict, dict):
            try:
                self._state = StateVector(**state_dict)
            except TypeError:
                self._state = None
        return True
