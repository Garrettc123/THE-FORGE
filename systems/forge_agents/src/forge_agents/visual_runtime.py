"""PS2-style visual runtime for displaying running forge_agents pipelines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .types import RunResult


@dataclass
class PS2VisualProfile:
    """Visual constraints that mimic a PS2-era HUD feel."""

    width: int = 640
    height: int = 448
    texture_filter: str = "nearest"
    fog_mode: str = "vertex-fog"
    post_fx: str = "dither+scanline"
    ui_theme: str = "blue-neon"
    audio_tone: str = "lofi-sci-fi"


@dataclass
class PerformanceBudget:
    """Simple runtime budget targets for the visual view."""

    frame_time_ms: float = 16.67
    memory_mb: float = 32.0
    draw_calls: int = 1200
    streaming_kbps: float = 1024.0


@dataclass
class RuntimeTelemetry:
    """Current telemetry snapshot for HUD diagnostics."""

    frame_time_ms: float = 0.0
    memory_mb: float = 0.0
    draw_calls: int = 0
    streaming_kbps: float = 0.0


class PS2AgentRuntimeView:
    """Live HUD renderer for planner/researcher/coder/critic execution."""

    def __init__(
        self,
        agent_order: Optional[List[str]] = None,
        profile: Optional[PS2VisualProfile] = None,
        budget: Optional[PerformanceBudget] = None,
    ) -> None:
        self.agent_order = agent_order or ["planner", "researcher", "coder", "critic"]
        self.profile = profile or PS2VisualProfile()
        self.budget = budget or PerformanceBudget()
        self.telemetry = RuntimeTelemetry()
        self.state = "BOOT"
        self.objective = ""
        self.stop_reason = ""
        self.active_agent: Optional[str] = None
        self.agent_states: Dict[str, Dict[str, str]] = {
            name: {"status": "idle", "message": "", "step": "0"} for name in self.agent_order
        }

    def begin(self, objective: str) -> None:
        self.state = "RUNNING"
        self.objective = objective
        self.stop_reason = ""

    def pause(self) -> None:
        if self.state == "RUNNING":
            self.state = "PAUSED"

    def resume(self) -> None:
        if self.state == "PAUSED":
            self.state = "RUNNING"

    def complete(self, stop_reason: str) -> None:
        if self.active_agent and self.active_agent in self.agent_states:
            self.agent_states[self.active_agent]["status"] = "complete"
        self.state = "COMPLETE"
        self.stop_reason = stop_reason
        self.active_agent = None

    def update_agent(self, agent: str, message: str, step_index: int) -> None:
        if self.state == "BOOT":
            self.state = "RUNNING"

        if self.active_agent and self.active_agent in self.agent_states:
            self.agent_states[self.active_agent]["status"] = "complete"

        if agent not in self.agent_states:
            self.agent_states[agent] = {"status": "idle", "message": "", "step": "0"}
            self.agent_order.append(agent)

        self.agent_states[agent]["status"] = "running"
        self.agent_states[agent]["message"] = _clean_line(message, 56)
        self.agent_states[agent]["step"] = str(step_index)
        self.active_agent = agent

    def set_telemetry(
        self,
        frame_time_ms: float,
        memory_mb: float,
        draw_calls: int,
        streaming_kbps: float,
    ) -> None:
        self.telemetry = RuntimeTelemetry(
            frame_time_ms=frame_time_ms,
            memory_mb=memory_mb,
            draw_calls=draw_calls,
            streaming_kbps=streaming_kbps,
        )

    def budget_report(self) -> Dict[str, bool]:
        report = {
            "frame_time_ok": self.telemetry.frame_time_ms <= self.budget.frame_time_ms,
            "memory_ok": self.telemetry.memory_mb <= self.budget.memory_mb,
            "draw_calls_ok": self.telemetry.draw_calls <= self.budget.draw_calls,
            "streaming_ok": self.telemetry.streaming_kbps <= self.budget.streaming_kbps,
        }
        report["overall_ok"] = all(report.values())
        return report

    def render_hud(self) -> str:
        budget_report = self.budget_report()
        lines = [
            "╔══════════════════ PS2 AGENT VIEW ══════════════════╗",
            f" RES: {self.profile.width}x{self.profile.height} | FILTER: {self.profile.texture_filter} | FX: {self.profile.post_fx}",
            f" STATE: {self.state} | THEME: {self.profile.ui_theme} | AUDIO: {self.profile.audio_tone}",
            f" OBJECTIVE: {_clean_line(self.objective, 52)}",
            "------------------------------------------------------",
        ]

        for agent in self.agent_order:
            info = self.agent_states[agent]
            marker = ">>" if info["status"] == "running" else "  "
            lines.append(
                f"{marker} {agent:<10} [{info['status']:^8}] s{info['step']:<3} {_clean_line(info['message'], 28)}"
            )

        lines.extend(
            [
                "------------------------------------------------------",
                (
                    " PERF "
                    f"frame={self.telemetry.frame_time_ms:.2f}ms "
                    f"mem={self.telemetry.memory_mb:.1f}MB "
                    f"draw={self.telemetry.draw_calls} "
                    f"stream={self.telemetry.streaming_kbps:.1f}kb/s"
                ),
                (
                    " BUDGET "
                    f"[frame:{_badge(budget_report['frame_time_ok'])}] "
                    f"[mem:{_badge(budget_report['memory_ok'])}] "
                    f"[draw:{_badge(budget_report['draw_calls_ok'])}] "
                    f"[stream:{_badge(budget_report['streaming_ok'])}] "
                    f"[overall:{_badge(budget_report['overall_ok'])}]"
                ),
                f" STOP: {self.stop_reason or 'n/a'}",
                "╚══════════════════════════════════════════════════════╝",
            ]
        )
        return "\n".join(lines)

    @classmethod
    def replay_frames(cls, result: RunResult) -> List[str]:
        view = cls()
        view.begin(result.task)
        frames: List[str] = []
        agent_messages = [m.content for m in result.transcript if m.role == "agent"]

        for index, step in enumerate(result.steps, start=1):
            msg = agent_messages[index - 1] if index - 1 < len(agent_messages) else ""
            view.update_agent(step.agent, msg, index)
            view.set_telemetry(
                frame_time_ms=min(8.0 + index * 0.6, 20.0),
                memory_mb=min(6.0 + index * 1.5, 40.0),
                draw_calls=min(100 + index * 80, 1600),
                streaming_kbps=min(50 + index * 25, 1400),
            )
            frames.append(view.render_hud())

        view.complete(result.stop_reason.upper())
        frames.append(view.render_hud())
        return frames

    @classmethod
    def render_run_result(cls, result: RunResult) -> str:
        return cls.replay_frames(result)[-1]


def _badge(flag: bool) -> str:
    return "OK" if flag else "FAIL"


def _clean_line(text: str, width: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= width:
        return cleaned
    return cleaned[: max(0, width - 3)] + "..."
