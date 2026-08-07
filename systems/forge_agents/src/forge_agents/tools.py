"""Tool registry with a few safe built-ins.

Design goals:
- Tools are plain callables wrapped by `Tool` with a name, description, and JSON-shape args.
- The registry is explicit; nothing is auto-registered besides opt-in built-ins.
- Built-ins avoid dangerous operations by default. `http_fetch` requires the `http` extra.
"""
from __future__ import annotations

import ast
import operator as op
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .types import ToolResult


@dataclass
class Tool:
    """A named callable exposed to agents."""
    name: str
    description: str
    func: Callable[..., Any]

    def call(self, **kwargs: Any) -> ToolResult:
        try:
            output = self.func(**kwargs)
            return ToolResult(tool=self.name, ok=True, output=output)
        except Exception as exc:  # noqa: BLE001 - surface the message to the agent
            return ToolResult(tool=self.name, ok=False, error=f"{type(exc).__name__}: {exc}")


class ToolRegistry:
    """Simple name -> Tool mapping."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> list[dict]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ---------------------------------------------------------------------------
# Built-in tools
# ---------------------------------------------------------------------------

def _read_file(path: str, max_bytes: int = 64_000) -> str:
    """Read a UTF-8 text file, truncated to max_bytes."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    data = p.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


# Safe arithmetic evaluator: numbers + + - * / // % ** and unary - +.
_ALLOWED_BIN = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod, ast.Pow: op.pow,
}
_ALLOWED_UNARY = {ast.UAdd: op.pos, ast.USub: op.neg}


def _safe_arith(expression: str) -> float:
    """Evaluate a purely arithmetic expression. No names, no calls."""
    tree = ast.parse(expression, mode="eval")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN:
            return _ALLOWED_BIN[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](_eval(node.operand))
        raise ValueError(f"Disallowed expression element: {ast.dump(node)}")

    return _eval(tree)


def _http_fetch(url: str, timeout: float = 10.0, max_bytes: int = 200_000) -> str:
    """Fetch a URL as text. Requires the optional `httpx` extra."""
    try:
        import httpx  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "http_fetch requires the 'http' extra: pip install forge-agents[http]"
        ) from exc
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("Only http(s) URLs are allowed")
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.text[:max_bytes]


def default_registry(*, enable_http: bool = False) -> ToolRegistry:
    """Return a registry populated with the safe built-ins."""
    reg = ToolRegistry()
    reg.register(Tool(
        name="read_file",
        description="Read a UTF-8 text file. Args: path (str), max_bytes (int, optional).",
        func=_read_file,
    ))
    reg.register(Tool(
        name="calc",
        description="Evaluate a pure arithmetic expression. Args: expression (str).",
        func=_safe_arith,
    ))
    if enable_http:
        reg.register(Tool(
            name="http_fetch",
            description="GET an http(s) URL and return the response body as text.",
            func=_http_fetch,
        ))
    return reg
