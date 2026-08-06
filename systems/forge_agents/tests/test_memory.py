from forge_agents.memory import Scratchpad, Transcript
from forge_agents.types import Message


def test_transcript_add_and_filter():
    t = Transcript()
    t.add(Message(role="user", content="hi"))
    t.add(Message(role="agent", content="hello", name="coder"))
    t.add(Message(role="tool", content="42", name="calc"))
    assert len(t) == 3
    assert [m.role for m in t.by_role("agent")] == ["agent"]
    assert t.last(2)[0].role == "agent"
    assert t.last(0) == []


def test_scratchpad_roundtrip():
    s = Scratchpad()
    s.set("k", 1)
    s.update({"a": [1, 2], "b": "x"})
    assert s.get("k") == 1
    assert "a" in s
    snap = s.snapshot()
    assert snap == {"k": 1, "a": [1, 2], "b": "x"}
    # snapshot is a copy
    snap["k"] = 99
    assert s.get("k") == 1
