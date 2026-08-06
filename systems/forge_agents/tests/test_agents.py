from forge_agents.agents import Coder, Planner, _parse_response
from forge_agents.memory import Scratchpad, Transcript
from forge_agents.providers import EchoProvider
from forge_agents.tools import default_registry


def test_parse_response_structured():
    text = "THOUGHT: think hard\nTOOL: calc {\"expression\": \"1+1\"}\nANSWER: two"
    thought, tool_call, answer = _parse_response(text)
    assert thought == "think hard"
    assert tool_call is not None and tool_call.tool == "calc"
    assert tool_call.args == {"expression": "1+1"}
    assert answer == "two"


def test_parse_response_freeform():
    thought, tool_call, answer = _parse_response("just a plain sentence")
    assert thought == ""
    assert tool_call is None
    assert answer == "just a plain sentence"


def test_planner_step_records_answer():
    p = Planner(provider=EchoProvider())
    t = Transcript()
    s = Scratchpad()
    step = p.step(t, s, task="write a haiku")
    assert step.agent == "planner"
    assert step.tool_call is None
    # Planner appended an agent message to the transcript.
    assert any(m.role == "agent" and m.name == "planner" for m in t.all())


def test_coder_uses_tool_when_scripted():
    script = {
        "coder": ['THOUGHT: try tool\nTOOL: calc {"expression": "6*7"}\nANSWER: 42'],
    }
    coder = Coder(provider=EchoProvider(script=script), tools=default_registry())
    t = Transcript()
    step = coder.step(t, Scratchpad(), task="compute 6*7")
    assert step.tool_call is not None and step.tool_call.tool == "calc"
    assert step.tool_result is not None and step.tool_result.ok
    assert step.tool_result.output == 42
    # A tool message was appended after the agent message.
    roles = [(m.role, m.name) for m in t.all()]
    assert ("agent", "coder") in roles
    assert ("tool", "calc") in roles
