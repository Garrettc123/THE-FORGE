#!/usr/bin/env python3
"""
Minimal FORGE cognitive core.
Provides the public API expected by forge_all.py and forge_garcar_bridge.py.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROTOCOL = "FORGE-COGNITIVE-CONTROL-v3"
FORGE_VERSION = "3.0"


def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


@dataclass
class AgentStatus:
    name: str
    status: str = "ready"
    last_update: str = field(default_factory=utc_iso)

    def report(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReplicationGate:
    enabled: bool = False
    reason: str = "dry-run safe mode"
    last_review: str = field(default_factory=utc_iso)


@dataclass
class StateVector:
    cash: float = 500_000.0
    mrr: float = 100_000.0
    revenue: float = 1_200_000.0
    profit: float = 40_000.0
    customers: int = 420
    churn: float = 0.03
    cac: float = 1_200.0
    assets: float = 250_000.0
    risk_score: float = 0.42
    capacity: float = 0.70
    infrastructure: float = 0.85
    productivity: float = 1.10


class Forge:
    def __init__(self) -> None:
        self.cycle_count = 0
        self.state = StateVector()
        self.replication_gate = ReplicationGate()
        self.sentinel = AgentStatus("SENTINEL")
        self.delta = AgentStatus("DELTA")
        self.treasury = AgentStatus("TREASURY")
        self.alpha = AgentStatus("ALPHA")
        self.beta = AgentStatus("BETA")
        self.gamma = AgentStatus("GAMMA")
        self.knowledge = AgentStatus("KNOWLEDGE")
        self.executive = AgentStatus("EXECUTIVE")

    def run_cycle(
        self,
        external_signals: Optional[List[Dict[str, Any]]] = None,
        initial_state: Optional[StateVector] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        if initial_state is not None:
            self.state = initial_state
        self.cycle_count += 1
        signals = list(external_signals or [])
        priorities = [signal.get("title") or signal.get("kind") or "signal" for signal in signals]
        return {
            "cycle": self.cycle_count,
            "timestamp": utc_iso(),
            "dry_run": dry_run,
            "event_count": len(signals),
            "priority_queue": priorities,
            "control_tower": self._control_tower(dry_run=dry_run, signals=signals),
            "phases": {
                "perception": {"signals_seen": len(signals)},
                "prediction": {"scenarios_considered": max(1, len(signals))},
                "decision": {"selected_actions": priorities[:3]},
                "action": {"executed": [] if dry_run else priorities[:1]},
                "outcome": {"status": "simulated" if dry_run else "executed"},
                "learning": {
                    "causal_updates": [],
                    "open_experiments": len(signals),
                    "closed_experiments": 0,
                },
            },
        }

    def demo_scenario(self, live: bool = False) -> Dict[str, Any]:
        result = self.run_cycle(
            external_signals=[
                {
                    "kind": "opportunity",
                    "title": "Demo scenario: validate strategic expansion",
                    "horizon": "H2",
                }
            ],
            dry_run=not live,
        )
        result["horizon_scorecards"] = [
            {
                "description": "Demo scenario: validate strategic expansion",
                "horizon": "H2",
                "utility": 0.78,
                "by_horizon": {"H1": 0.52, "H2": 0.78, "H3": 0.71, "H4": 0.66},
            }
        ]
        return result

    def dump_state(self, path: Path) -> None:
        snapshot = {
            "protocol": PROTOCOL,
            "forge_version": FORGE_VERSION,
            "cycle_count": self.cycle_count,
            "state": asdict(self.state),
            "replication_gate": asdict(self.replication_gate),
            "generated_at": utc_iso(),
        }
        path.write_text(__import__('json').dumps(snapshot, indent=2), encoding='utf-8')

    def load_state(self, path: Path) -> bool:
        if not path.exists():
            return False
        import json
        data = json.loads(path.read_text(encoding='utf-8'))
        self.cycle_count = int(data.get("cycle_count", 0))
        state_data = data.get("state") or {}
        self.state = StateVector(**{**asdict(StateVector()), **state_data})
        gate_data = data.get("replication_gate") or {}
        self.replication_gate = ReplicationGate(**{
            "enabled": gate_data.get("enabled", False),
            "reason": gate_data.get("reason", "dry-run safe mode"),
            "last_review": gate_data.get("last_review", utc_iso()),
        })
        return True

    def _control_tower(self, dry_run: bool, signals: List[Dict[str, Any]]) -> str:
        mode = "DRY-RUN" if dry_run else "LIVE"
        return (
            f"[FORGE CONTROL TOWER] cycle={self.cycle_count} mode={mode} "
            f"signals={len(signals)} cash=${self.state.cash:,.0f} mrr=${self.state.mrr:,.0f}"
        )
