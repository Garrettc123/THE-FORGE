import pytest

from forge_agents.tools import Tool, ToolRegistry, default_registry


def test_registry_register_and_lookup():
    reg = ToolRegistry()
    reg.register(Tool(name="echo", description="", func=lambda x: x))
    assert "echo" in reg
    assert reg.get("echo") is not None
    assert reg.names() == ["echo"]
    with pytest.raises(ValueError):
        reg.register(Tool(name="echo", description="", func=lambda x: x))


def test_calc_tool_basic():
    reg = default_registry()
    calc = reg.get("calc")
    assert calc is not None
    res = calc.call(expression="2 + 3 * 4")
    assert res.ok and res.output == 14
    res = calc.call(expression="2 ** 10")
    assert res.ok and res.output == 1024


def test_calc_tool_rejects_names():
    reg = default_registry()
    res = reg.get("calc").call(expression="__import__('os').system('x')")
    assert not res.ok
    assert "Disallowed" in (res.error or "") or "invalid" in (res.error or "").lower()


def test_read_file_tool(tmp_path):
    reg = default_registry()
    p = tmp_path / "sample.txt"
    p.write_text("hello world", encoding="utf-8")
    res = reg.get("read_file").call(path=str(p))
    assert res.ok and res.output == "hello world"


def test_read_file_missing():
    reg = default_registry()
    res = reg.get("read_file").call(path="/nonexistent/path/xyzzy.txt")
    assert not res.ok
    assert "FileNotFoundError" in (res.error or "")


def test_default_registry_http_opt_in():
    assert "http_fetch" not in default_registry()
    assert "http_fetch" in default_registry(enable_http=True)
