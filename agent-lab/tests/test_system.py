import asyncio
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.agent import run, parse
from app.evaluation import load_dataset, check
from app.providers import ReplayProvider
from app.tools import query_sales
from app.judge import calibrate
from app.main import app

@pytest.mark.parametrize("case",load_dataset()["cases"],ids=lambda c:c["id"])
def test_v2_golden_cases(case):
    result=asyncio.run(run(case,ReplayProvider(),"v2"))
    assert all(x["passed"] for x in check(case["expected"],result))
    assert 1<=result["attempt"]<=3

@pytest.mark.parametrize("sql",["DROP TABLE sales","DELETE FROM sales", "PRAGMA table_info(sales)",
    "SELECT name FROM sqlite_master", "SELECT * FROM products", "ATTACH DATABASE ':memory:' AS other",
    "SELECT * FROM sales; DELETE FROM sales", "SELECT load_extension('x')"])
def test_database_rejects_out_of_scope(sql):
    with pytest.raises(sqlite3.Error):
        query_sales(sql)
    assert query_sales("SELECT SUM(amount) AS total FROM sales")==[{"total":440.0}]

def test_repeated_failed_valid_action_stops_early():
    case={"target":"data","responses":[json.dumps({"tool":"query_sales","arguments":{"sql":"SELECT missing FROM sales"}})]}
    result=asyncio.run(run(case,ReplayProvider(),"v2"))
    assert result["status"]=="loop_stopped"
    assert result["attempt"]==2

def test_unknown_tool_cannot_execute():
    case={"target":"customer","responses":['{"tool":"send_email","arguments":{}}']}
    result=asyncio.run(run(case,ReplayProvider(),"v2"))
    assert result["status"]=="blocked"
    assert not any(x["node"]=="execute" for x in result["trace"])

def test_memory_is_not_shared_between_runs():
    original=next(c for c in load_dataset()["cases"] if c["id"]=="customer-memory")
    first=asyncio.run(run(original,ReplayProvider(),"v2"))
    second=asyncio.run(run({**original,"memory":{}},ReplayProvider(),"v2"))
    assert first["output"]["product"]=="柠檬红茶"
    assert second["output"]["product"] is None

def test_metric_catches_correct_status_wrong_value():
    assert not all(c["passed"] for c in check({"status":"success","subset":{"price":7.5}}, {"status":"success","output":{"price":100}}))

def test_extra_protocol_fields_rejected():
    with pytest.raises(ValueError):
        parse('{"tool":"handoff","arguments":{},"execute_shell":"no"}',True)

def test_calibration_requires_human_provenance():
    with pytest.raises(ValueError):
        calibrate([],[])
    with pytest.raises(ValueError):
        calibrate([], [{"id":str(i),"source":"machine"} for i in range(3)])

def test_calibration_computes_mae_and_rejects_wrong_snapshot():
    machine=[{"id":str(i),"target":"customer","output_id":str(i)+":v2","judgement":{"scores":[{"key":"grounding","score":4}]}} for i in range(3)]
    human=[{"id":str(i),"source":"human","annotator":"test-fixture","output_id":str(i)+":v2","scores":{"grounding":3}} for i in range(3)]
    result=calibrate(machine,human)
    assert result["mae"]==1 and not result["passed"]
    human[0]["output_id"]="wrong"
    with pytest.raises(ValueError):
        calibrate(machine,human)

def test_api_and_design_dataset_binding():
    with TestClient(app) as client:
        assert client.get("/health").status_code==200
        dataset=client.get("/api/datasets").json()
        designs=client.get("/api/designs").json()
        assert len(designs)==3
        assert sum(len(d["bound_cases"]) for d in designs)==15
        assert all(d["dataset_fingerprint"]==dataset["fingerprint"] for d in designs)
        assert client.get("/").status_code==200
