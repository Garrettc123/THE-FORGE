#!/usr/bin/env python3
"""
FORGE ↔ Garcar Bridge
=====================
Runs Garcar status modules (when secrets present) and feeds the resulting
economic signals into one FORGE cognitive cycle.

Usage:
  python forge_garcar_bridge.py --dry-run
  python forge_garcar_bridge.py --mode full
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports (same directory)
from forge_cognitive_core import (
    Forge,
    StateVector,
    utc_iso,
    FORGE_VERSION,
    PROTOCOL,
)

# Optional Garcar import – degrade gracefully if not present or tokens missing
try:
    import garcar_master as gm
    HAS_GARCAR = True
except ImportError:
    HAS_GARCAR = False


def collect_garcar_signals(dry_run: bool = True) -> Dict[str, Any]:
    """Run Garcar status-mode modules and map outputs into Forge signals."""
    if not HAS_GARCAR:
        return {"source": "none", "signals": [], "state": None}

    # Re-use Garcar's own modules without full orchestration side-effects
    briefing = gm.morning_briefing(dry_run=True)
    github = gm.github_repo_audit(dry_run=True)
    stripe = gm.stripe_revenue_check(dry_run=True)
    linear = gm.linear_issues_sync(dry_run=True)

    signals: List[Dict[str, Any]] = []

    # Linear P1 → risk / opportunity signals
    for issue in (linear.get("p1_urgent") or []):
        signals.append({
            "kind": "risk",
            "title": f"Linear P1: {issue.get('title', issue.get('id'))}",
            "source": "linear",
            "mitigation_cost": 2_000,
            "avoided_loss": 15_000,
            "metadata": issue,
        })
    for issue in (linear.get("in_progress") or [])[:5]:
        signals.append({
            "kind": "opportunity",
            "title": f"In-progress: {issue.get('title', issue.get('id'))}",
            "type": "VALIDATE",
            "estimated_capital": 1_500,
            "expected_value": 8_000,
            "info_value": 0.5,
            "source": "linear",
            "metadata": issue,
        })

    # GitHub stale / hub issues
    for issue in (github.get("systems_master_hub_open_issues") or [])[:5]:
        signals.append({
            "kind": "opportunity",
            "title": f"Hub issue #{issue.get('number')}: {issue.get('title')}",
            "type": "VALIDATE",
            "estimated_capital": 1_000,
            "expected_value": 5_000,
            "source": "github",
            "metadata": issue,
        })

    # Build StateVector from Stripe when available
    state: Optional[StateVector] = None
    if not stripe.get("skipped"):
        mrr = float(stripe.get("mrr_usd") or 0)
        cash = float(stripe.get("available_usd") or 0) + float(stripe.get("pending_usd") or 0)
        state = StateVector(
            cash=cash if cash > 0 else 500_000,
            mrr=mrr if mrr > 0 else 100_000,
            revenue=mrr * 12 if mrr > 0 else 1_200_000,
            profit=mrr * 0.4 if mrr > 0 else 40_000,
            customers=max(1, int(mrr / 250)) if mrr else 420,
            churn=0.03,
            cac=1_200,
            assets=250_000,
            risk_score=0.42,
            capacity=0.7,
            infrastructure=0.85,
            productivity=1.1,
        )

    return {
        "source": "garcar",
        "briefing": briefing,
        "github_summary": {
            "total": github.get("total_repos"),
            "active": github.get("active_count"),
            "stale": github.get("stale_count"),
        },
        "stripe": {k: v for k, v in stripe.items() if k != "last_10_charges"},
        "linear_p1": len(linear.get("p1_urgent") or []),
        "signals": signals,
        "state": state,
    }


def run_bridge(mode: str = "cycle", dry_run: bool = True) -> Dict[str, Any]:
    garcar_data = collect_garcar_signals(dry_run=dry_run)
    forge = Forge()

    external = garcar_data.get("signals") or None
    initial = garcar_data.get("state")

    result = forge.run_cycle(
        external_signals=external,
        initial_state=initial,
        dry_run=dry_run,
    )

    result["garcar_feed"] = {
        "source": garcar_data.get("source"),
        "signal_count": len(garcar_data.get("signals") or []),
        "github_summary": garcar_data.get("github_summary"),
        "stripe": garcar_data.get("stripe"),
        "linear_p1": garcar_data.get("linear_p1"),
    }
    result["protocol"] = PROTOCOL
    result["forge_version"] = FORGE_VERSION
    result["bridge_mode"] = mode
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="FORGE ↔ Garcar Bridge")
    parser.add_argument("--mode", choices=["cycle", "full"], default="cycle")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Disable dry-run")
    parser.add_argument("--output", default="forge_garcar_bridge_output.json")
    args = parser.parse_args()

    dry = not args.live
    try:
        result = run_bridge(mode=args.mode, dry_run=dry)
        Path(args.output).write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

        print(result.get("control_tower", ""))
        print()
        print(f"[BRIDGE] Garcar feed source : {result['garcar_feed']['source']}")
        print(f"[BRIDGE] Signals injected   : {result['garcar_feed']['signal_count']}")
        print(f"[BRIDGE] Cycle complete     → {Path(args.output).resolve()}")
        print(f"[BRIDGE] Events             : {result.get('event_count')}")
        print(f"[BRIDGE] Priority queue     : {len(result.get('priority_queue', []))}")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
