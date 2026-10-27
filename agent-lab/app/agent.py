"""v1 strict linear baseline; v2 bounded LangGraph with traceable validation/repair."""
import json
import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.tools import ALLOWED, SCHEMAS, execute


class State(TypedDict, total=False):
    case: dict
    provider: object
    attempt: int
    raw: str
    action: dict
    output: object
    error: str
    status: str
    trace: list[dict]
    seen: list[str]
    version: str


def log(state, node, **detail):
    return state.get("trace", []) + [{"node": node, **detail}]


def parse(raw, repair=False):
    if repair:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    obj = json.loads(raw)
    if not isinstance(obj, dict) or set(obj) != {"tool", "arguments"}:
        raise ValueError("action requires exactly tool and arguments")
    if not isinstance(obj["tool"], str) or not isinstance(obj["arguments"], dict):
        raise ValueError("invalid action types")
    return obj


async def plan(s):
    attempt = s.get("attempt", 0) + 1
    try:
        raw = await s["provider"].action(s["case"], attempt, s.get("error", ""))
        return {"attempt": attempt, "raw": raw, "error": "", "trace": log(s, "plan", attempt=attempt, raw=raw)}
    except Exception as exc:
        return {"attempt": attempt, "raw": "", "error": type(exc).__name__, "status": "provider_error", "trace": log(s, "plan", error=type(exc).__name__)}


def validate(s):
    if s.get("status") == "provider_error":
        return {}
    try:
        action = parse(s["raw"], repair=True)
        if action["tool"] not in ALLOWED[s["case"]["target"]]:
            return {"status": "blocked", "error": "tool_not_allowed", "trace": log(s, "validate", rejected="tool_not_allowed")}
        args = SCHEMAS[action["tool"]].model_validate(action["arguments"]).model_dump()
        action["arguments"] = args
        signature = json.dumps(action, sort_keys=True, ensure_ascii=False)
        if signature in s.get("seen", []):
            return {"status": "loop_stopped", "error": "repeated_failed_action", "trace": log(s, "validate", rejected="repeated_failed_action")}
        return {"action": action, "status": "ready", "error": "", "seen": s.get("seen", []) + [signature], "trace": log(s, "validate", accepted=True)}
    except (ValueError, TypeError) as exc:
        return {"status": "retry", "error": str(exc)[:450], "trace": log(s, "validate", error=str(exc)[:450])}


def act(s):
    action = s["action"]
    try:
        output = execute(action["tool"], action["arguments"], s["case"].get("memory", {}))
        return {"output": output, "status": "success", "trace": log(s, "execute", tool=action["tool"], arguments=action["arguments"], observation=output)}
    except Exception as exc:
        # The database boundary remains active in both versions.
        if "authoriz" in str(exc).lower() or "readonly" in str(exc).lower():
            return {"status": "blocked", "error": "database_access_denied", "trace": log(s, "execute", rejected="database_access_denied")}
        return {"status": "retry", "error": str(exc)[:300], "trace": log(s, "execute", error=str(exc)[:300])}


def finish(s):
    return {"status": "exhausted" if s["status"] == "retry" else s["status"], "trace": log(s, "finish", attempts=s["attempt"])}


def next_after_validation(s):
    if s["status"] == "ready":
        return "execute"
    return "plan" if s["status"] == "retry" and s["attempt"] < 3 else "finish"


def next_after_execution(s):
    return "plan" if s["status"] == "retry" and s["attempt"] < 3 else "finish"


builder = StateGraph(State)
for name, node in [("plan", plan), ("validate", validate), ("execute", act), ("finish", finish)]:
    builder.add_node(name, node)
builder.add_edge(START, "plan")
builder.add_edge("plan", "validate")
builder.add_conditional_edges("validate", next_after_validation, ["execute", "plan", "finish"])
builder.add_conditional_edges("execute", next_after_execution, ["plan", "finish"])
builder.add_edge("finish", END)
graph = builder.compile()


async def run(case, provider, version):
    state = {"case": case, "provider": provider, "attempt": 0, "trace": [], "seen": [], "status": "initial"}
    if version == "v2":
        result = await graph.ainvoke(state, {"recursion_limit": 20})
    else:
        state.update(await plan(state))
        try:
            action = parse(state["raw"])
            if action["tool"] not in SCHEMAS:
                raise ValueError("unknown tool")
            state["action"] = action
            state.update(act(state))
        except Exception as exc:
            state.update(status="error", error=str(exc)[:300])
        result = state
    return {k: result.get(k) for k in ("status", "output", "error", "attempt", "trace")}
