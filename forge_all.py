#!/usr/bin/env python3
"""
THE FORGE + Garcar — Unified Master Launcher
=============================================
One entry point for the entire cognitive economic control system.

Usage:
  python forge_all.py                  # interactive menu
  python forge_all.py status           # all agent + garcar status
  python forge_all.py cycle            # one Forge cognitive cycle (dry-run)
  python forge_all.py cycle --live     # live cycle (capital can move)
  python forge_all.py bridge           # Garcar → Forge bridge (dry-run)
  python forge_all.py bridge --live
  python forge_all.py garcar           # Garcar master status
  python forge_all.py garcar full      # Garcar full orchestration
  python forge_all.py tower            # Control Tower only
  python forge_all.py dump             # write full state snapshot
  python forge_all.py protocol         # print protocol summary
  python forge_all.py demo             # full-loop demo + horizon scores
  python forge_all.py demo --live
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# --- Bootstrap: expand compressed core or fail clearly ---
def _ensure_core():
    import subprocess
    core = ROOT / "forge_cognitive_core.py"
    if core.exists() and core.stat().st_size > 1000:
        return
    expander = ROOT / "expand_core.py"
    if expander.exists():
        subprocess.check_call([sys.executable, str(expander)])
        if core.exists() and core.stat().st_size > 1000:
            return
    raise SystemExit(
        "ERROR: forge_cognitive_core.py missing.\n"
        "Run: python expand_core.py\n"
        "Or copy forge_cognitive_core.py from FORGE_COMPLETE_v3.zip into this directory."
    )

_ensure_core()

def cmd_status() -> None:
    from forge_cognitive_core import Forge, PROTOCOL, FORGE_VERSION, asdict
    forge = Forge()
    out = {
        "protocol": PROTOCOL,
        "version": FORGE_VERSION,
        "agents": [
            forge.sentinel.report(),
            forge.delta.report(),
            forge.treasury.report(),
            forge.alpha.report(),
            forge.beta.report(),
            forge.gamma.report(),
            forge.knowledge.report(),
            forge.executive.report(),
        ],
        "replication_gate": asdict(forge.replication_gate),
    }
    try:
        import garcar_master as gm
        briefing = gm.morning_briefing(dry_run=True)
        out["garcar_env"] = briefing.get("env_status", {})
    except Exception as e:
        out["garcar_env"] = {"error": str(e)}
    print(json.dumps(out, indent=2, default=str))

def cmd_cycle(live: bool = False) -> None:
    from forge_cognitive_core import Forge
    forge = Forge()
    result = forge.run_cycle(dry_run=not live)
    Path("forge_run_output.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    forge.dump_state(Path("forge_state_snapshot.json"))
    print(result.get("control_tower", ""))
    print()
    print(f"[FORGE] Cycle {result['cycle']} complete")
    print(f"[FORGE] Events: {result.get('event_count')}  Queue: {len(result.get('priority_queue', []))}")
    print(f"[FORGE] Mode: {'LIVE' if live else 'DRY-RUN'}")

def cmd_bridge(live: bool = False) -> None:
    from forge_garcar_bridge import run_bridge
    result = run_bridge(mode="cycle", dry_run=not live)
    Path("forge_garcar_bridge_output.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    print(result.get("control_tower", ""))
    print()
    print(f"[BRIDGE] Source: {result['garcar_feed']['source']}")
    print(f"[BRIDGE] Signals: {result['garcar_feed']['signal_count']}")
    print(f"[BRIDGE] Events: {result.get('event_count')}  Queue: {len(result.get('priority_queue', []))}")
    print(f"[BRIDGE] Mode: {'LIVE' if live else 'DRY-RUN'}")

def cmd_garcar(mode: str = "status", live: bool = False) -> None:
    import garcar_master as gm
    gm.run(mode=mode, dry_run=not live)

def cmd_tower() -> None:
    from forge_cognitive_core import Forge
    forge = Forge()
    result = forge.run_cycle(dry_run=True)
    print(result.get("control_tower", ""))

def cmd_dump() -> None:
    from forge_cognitive_core import Forge
    forge = Forge()
    forge.run_cycle(dry_run=True)
    path = Path("forge_state_snapshot.json")
    forge.dump_state(path)
    print(f"[FORGE] Full state written → {path.resolve()}")

def cmd_protocol() -> None:
    proto = ROOT / "FORGE_v3_PROTOCOL.md"
    if proto.exists():
        print(proto.read_text(encoding="utf-8"))
    else:
        print("FORGE_v3_PROTOCOL.md not found")

def cmd_demo(live: bool = False) -> None:
    from forge_cognitive_core import Forge
    forge = Forge()
    snap = Path("forge_state_snapshot.json")
    if snap.exists():
        loaded = forge.load_state(snap)
        print(f"[DEMO] Prior state loaded: {loaded} (cycle={forge.cycle_count})")
    result = forge.demo_scenario(live=live)
    Path("forge_run_output.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    forge.dump_state(Path("forge_state_snapshot.json"))
    print(result.get("control_tower", ""))
    print()
    print("[DEMO] Horizon scorecards (top candidates):")
    for sc in result.get("horizon_scorecards", []):
        print(f"  • {sc['description']}")
        print(f"    native={sc['horizon']}  utility={sc['utility']}  by_H={sc['by_horizon']}")
    print()
    learning = result.get("phases", {}).get("learning", {})
    print(f"[DEMO] Causal updates : {learning.get('causal_updates', [])}")
    print(f"[DEMO] Open experiments: {learning.get('open_experiments')}  Closed: {learning.get('closed_experiments')}")
    print(f"[DEMO] Outcome        : {result.get('phases', {}).get('outcome', {})}")
    print(f"[DEMO] Mode: {'LIVE' if live else 'DRY-RUN'}")

def interactive() -> None:
    menu = """
╔══════════════════════════════════════════════════╗
║     THE FORGE + Garcar — Unified Launcher        ║
╠══════════════════════════════════════════════════╣
║  1. status     All agents + Garcar env           ║
║  2. cycle      One cognitive cycle (dry-run)     ║
║  3. cycle --live   Cognitive cycle (live)        ║
║  4. bridge     Garcar → Forge bridge (dry-run)   ║
║  5. bridge --live  Bridge live                   ║
║  6. garcar     Garcar status                     ║
║  7. tower      Control Tower only                ║
║  8. dump       Full state snapshot               ║
║  9. protocol   Print operating protocol          ║
║  d. demo       Full-loop demo + horizon scores   ║
║  0. quit                                         ║
╚══════════════════════════════════════════════════╝
"""
    print(menu)
    choice = input("Select> ").strip().lower()
    if choice in ("1", "status"):
        cmd_status()
    elif choice in ("2", "cycle"):
        cmd_cycle(live=False)
    elif choice in ("3", "cycle --live", "live"):
        cmd_cycle(live=True)
    elif choice in ("4", "bridge"):
        cmd_bridge(live=False)
    elif choice in ("5", "bridge --live"):
        cmd_bridge(live=True)
    elif choice in ("6", "garcar"):
        cmd_garcar("status", live=False)
    elif choice in ("7", "tower"):
        cmd_tower()
    elif choice in ("8", "dump"):
        cmd_dump()
    elif choice in ("9", "protocol"):
        cmd_protocol()
    elif choice in ("d", "demo"):
        cmd_demo(live=False)
    elif choice in ("0", "quit", "q", "exit"):
        print("Bye.")
    else:
        print("Unknown selection.")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="THE FORGE + Garcar Unified Master Launcher"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        choices=["status", "cycle", "bridge", "garcar", "tower", "dump", "protocol", "demo"],
        help="Command to run (omit for interactive menu)",
    )
    parser.add_argument(
        "garcar_mode",
        nargs="?",
        default="status",
        choices=["status", "full", "audit", "deploy"],
        help="Garcar sub-mode (when command=garcar)",
    )
    parser.add_argument("--live", action="store_true", help="Disable dry-run")
    args = parser.parse_args()

    if args.command is None:
        interactive()
        return

    if args.command == "status":
        cmd_status()
    elif args.command == "cycle":
        cmd_cycle(live=args.live)
    elif args.command == "bridge":
        cmd_bridge(live=args.live)
    elif args.command == "garcar":
        cmd_garcar(mode=args.garcar_mode, live=args.live)
    elif args.command == "tower":
        cmd_tower()
    elif args.command == "dump":
        cmd_dump()
    elif args.command == "protocol":
        cmd_protocol()
    elif args.command == "demo":
        cmd_demo(live=args.live)

if __name__ == "__main__":
    main()
