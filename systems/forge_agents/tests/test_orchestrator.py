from forge_agents.orchestrator import Orchestrator, RunBudget, StopReason
from forge_agents.providers import EchoProvider


def test_orchestrator_default_run_approves():
    # EchoProvider's default critic response is APPROVED, so it should stop cleanly.
    orch = Orchestrator(provider=EchoProvider())
    result = orch.run("write a friendly greeting")
    assert result.stop_reason == StopReason.APPROVED.value
    assert result.step_count >= 4  # planner, researcher, coder, critic
    assert result.final_answer  # coder produced something
    assert result.elapsed_seconds >= 0


def test_orchestrator_revision_loop_then_gives_up():
    # Force the critic to keep asking for revisions; budget limits revisions to 1.
    script = {
        "critic": [
            "THOUGHT: not good\nANSWER: REVISE: needs more detail",
            "THOUGHT: still no\nANSWER: REVISE: nope",
            "THOUGHT: still no\nANSWER: REVISE: nope",
        ],
    }
    orch = Orchestrator(
        provider=EchoProvider(script=script),
        budget=RunBudget(max_steps=20, max_seconds=10, max_revisions=1),
    )
    result = orch.run("do a thing")
    assert result.stop_reason in (
        StopReason.NO_PROGRESS.value,
        StopReason.MAX_STEPS.value,
    )


def test_orchestrator_respects_max_steps():
    orch = Orchestrator(
        provider=EchoProvider(script={"critic": ["ANSWER: REVISE: no"] * 20}),
        budget=RunBudget(max_steps=3, max_seconds=10, max_revisions=99),
    )
    result = orch.run("task")
    assert result.step_count <= 3
    assert result.stop_reason == StopReason.MAX_STEPS.value


def test_final_answer_comes_from_coder():
    script = {
        "coder": ["THOUGHT: t\nANSWER: THE FINAL DRAFT"],
        "critic": ["THOUGHT: ok\nANSWER: APPROVED"],
    }
    orch = Orchestrator(provider=EchoProvider(script=script))
    result = orch.run("hello")
    assert result.final_answer == "THE FINAL DRAFT"
    assert result.stop_reason == StopReason.APPROVED.value
