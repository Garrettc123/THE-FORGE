from forge_agents.orchestrator import Orchestrator
from forge_agents.providers import EchoProvider
from forge_agents.visual_runtime import PS2AgentRuntimeView


def test_render_run_result_contains_ps2_hud_and_completion():
    result = Orchestrator(provider=EchoProvider()).run("Build a short launch plan")
    hud = PS2AgentRuntimeView.render_run_result(result)
    assert "PS2 AGENT VIEW" in hud
    assert "STATE: COMPLETE" in hud
    assert "planner" in hud
    assert "critic" in hud
    assert "overall:OK" in hud


def test_replay_frames_follow_step_count():
    result = Orchestrator(provider=EchoProvider()).run("Produce one sentence")
    frames = PS2AgentRuntimeView.replay_frames(result)
    assert len(frames) == result.step_count + 1
    assert "[running]" in frames[0]
    assert "STOP: APPROVED" in frames[-1]


def test_budget_report_fails_when_telemetry_exceeds_limits():
    view = PS2AgentRuntimeView()
    view.set_telemetry(
        frame_time_ms=33.4,
        memory_mb=64.0,
        draw_calls=2000,
        streaming_kbps=2048.0,
    )
    report = view.budget_report()
    assert report["frame_time_ok"] is False
    assert report["memory_ok"] is False
    assert report["draw_calls_ok"] is False
    assert report["streaming_ok"] is False
    assert report["overall_ok"] is False
