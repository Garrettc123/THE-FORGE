"""CLI entry point: `python -m forge_agents.cli run "your task"` or `forge-agents run ...`."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .orchestrator import Orchestrator, RunBudget
from .providers import EchoProvider
from .tools import default_registry
from .visual_runtime import PS2AgentRuntimeView


def _cmd_run(args: argparse.Namespace) -> int:
    provider = EchoProvider()  # Only offline provider is bundled.
    tools = default_registry(enable_http=args.enable_http)
    budget = RunBudget(
        max_steps=args.max_steps,
        max_seconds=args.max_seconds,
        max_revisions=args.max_revisions,
    )
    orch = Orchestrator(provider=provider, tools=tools, budget=budget)
    result = orch.run(args.task)

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.ps2_view:
        if args.ps2_replay:
            for i, frame in enumerate(PS2AgentRuntimeView.replay_frames(result), start=1):
                print(f"[frame {i}]")
                print(frame)
                print()
        else:
            print(PS2AgentRuntimeView.render_run_result(result))
            print("---")
            print(result.final_answer)
    else:
        print(f"[forge-agents] stop_reason={result.stop_reason} "
              f"steps={result.step_count} elapsed={result.elapsed_seconds}s")
        print("---")
        print(result.final_answer)
    return 0


def _cmd_tools(_args: argparse.Namespace) -> int:
    reg = default_registry(enable_http=True)
    for entry in reg.describe():
        print(f"- {entry['name']}: {entry['description']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forge-agents")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run the orchestrator on a task.")
    p_run.add_argument("task", help="Free-form task description.")
    p_run.add_argument("--max-steps", type=int, default=12)
    p_run.add_argument("--max-seconds", type=float, default=60.0)
    p_run.add_argument("--max-revisions", type=int, default=3)
    p_run.add_argument("--enable-http", action="store_true", help="Enable http_fetch tool.")
    p_run.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    p_run.add_argument("--ps2-view", action="store_true", help="Render a PS2-style HUD view.")
    p_run.add_argument("--ps2-replay", action="store_true", help="Show per-step HUD replay.")
    p_run.set_defaults(func=_cmd_run)

    p_tools = sub.add_parser("tools", help="List available tools.")
    p_tools.set_defaults(func=_cmd_tools)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
