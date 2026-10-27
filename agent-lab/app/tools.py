"""Small local shop fixture. Every SQL query uses an isolated read-only connection."""
import json
import sqlite3
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProductArgs(Args):
    name: str = Field(min_length=1, max_length=80)


class QueryArgs(Args):
    sql: str = Field(min_length=1, max_length=1500)


class SceneArgs(Args):
    title: str = Field(min_length=2, max_length=80)
    goal: str = Field(min_length=5, max_length=300)
    roles: list[str] = Field(min_length=2, max_length=4)
    steps: list[str] = Field(min_length=3, max_length=5)


class HandoffArgs(Args):
    reason: str = Field(min_length=2, max_length=300)


class RecallArgs(Args):
    key: Literal["product"]


SCHEMAS = {"retrieve_product": ProductArgs, "query_sales": QueryArgs,
           "create_scene": SceneArgs, "handoff": HandoffArgs, "recall": RecallArgs}
ALLOWED = {"customer": {"retrieve_product", "recall", "handoff"},
           "data": {"query_sales"}, "scene": {"create_scene"}}


def database():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE products(name TEXT PRIMARY KEY, price REAL, stock INTEGER);
    INSERT INTO products VALUES ('茉莉绿茶',7.5,30),('乌龙茶',9.0,20),('柠檬红茶',8.0,15);
    CREATE TABLE sales(product TEXT, region TEXT, amount REAL, day TEXT);
    INSERT INTO sales VALUES ('茉莉绿茶','华北',75,'2026-09-03'),
    ('乌龙茶','华北',90,'2026-09-10'),('茉莉绿茶','华南',150,'2026-09-11'),
    ('柠檬红茶','华南',80,'2026-09-12'),('乌龙茶','华北',45,'2026-10-01');
    """)
    return db


def query_sales(sql):
    # Reject all writes, PRAGMA, attach and schema reads at SQLite authorization level.
    db = database()
    db.execute("PRAGMA query_only=ON")
    def authorize(action, arg1, arg2, _db, _trigger):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and arg1 == "sales":
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in {"sum", "count", "avg", "min", "max", "coalesce", "round"}:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    db.set_authorizer(authorize)
    budget = 0
    def limit():
        nonlocal budget
        budget += 1
        return int(budget > 100)
    db.set_progress_handler(limit, 1000)
    try:
        return [dict(row) for row in db.execute(sql).fetchmany(100)]
    finally:
        db.close()


def execute(tool, arguments, memory):
    if tool == "retrieve_product":
        with database() as db:
            row = db.execute("SELECT * FROM products WHERE name=?", (arguments["name"],)).fetchone()
        return dict(row) if row else {"found": False, "message": "未找到商品，不编造价格"}
    if tool == "query_sales":
        return query_sales(arguments["sql"])
    if tool == "create_scene":
        return SceneArgs.model_validate(arguments).model_dump()
    if tool == "handoff":
        return {"status": "handoff", "reason": arguments["reason"], "note": "教学沙箱，不发送外部工单"}
    if tool == "recall":
        return {"product": memory.get("product")}
    raise ValueError("unknown tool")


def tool_description(target):
    return json.dumps({name: SCHEMAS[name].model_json_schema() for name in sorted(ALLOWED[target])}, ensure_ascii=False)
