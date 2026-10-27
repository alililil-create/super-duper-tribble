import asyncio
import hashlib
import json
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal
from app.agent import run
from app.providers import ReplayProvider, QwenProvider

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "eval/datasets/shop-v1.json"
RESULTS = ROOT / "artifacts"


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    target: Literal["customer", "data", "scene"]
    title: str
    question: str
    responses: list[str] = Field(min_length=1)
    expected: dict
    tags: list[Literal["protocol", "tools", "correctness", "safety", "recovery"]]
    memory: dict = Field(default_factory=dict)


def load_dataset():
    raw = DATASET.read_bytes()
    data = json.loads(raw)
    data["cases"] = [Case.model_validate(c).model_dump() for c in data["cases"]]
    ids = [c["id"] for c in data["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case id")
    data["fingerprint"] = hashlib.sha256(raw).hexdigest()
    return data


def check(expected, result):
    checks = [{"name":"终止状态", "passed": result["status"] == expected["status"], "expected":expected["status"], "actual":result["status"]}]
    if "subset" in expected:
        out=result.get("output")
        for key, value in expected["subset"].items():
            actual=out.get(key) if isinstance(out,dict) else None
            checks.append({"name":key,"passed":actual==value,"expected":value,"actual":actual})
    if "equals" in expected:
        checks.append({"name":"数据查询结果","passed":result.get("output")==expected["equals"],"expected":expected["equals"],"actual":result.get("output")})
    if "attempt" in expected:
        checks.append({"name":"尝试次数","passed":result["attempt"]==expected["attempt"],"expected":expected["attempt"],"actual":result["attempt"]})
    return checks


async def evaluate(provider_name="replay"):
    data=load_dataset()
    provider=ReplayProvider() if provider_name=="replay" else QwenProvider()
    started=time.perf_counter()
    rows=[]
    for case in data["cases"]:
        row={k:case[k] for k in ("id","target","title","question","tags")}
        for version in ("v1","v2"):
            tick=time.perf_counter()
            result=await run(case,provider,version)
            result["elapsed_ms"]=round((time.perf_counter()-tick)*1000,2)
            result["checks"]=check(case["expected"],result)
            result["passed"]=all(c["passed"] for c in result["checks"])
            row[version]=result
        rows.append(row)
    counts={v:sum(r[v]["passed"] for r in rows) for v in ("v1","v2")}
    dimensions={tag:{v:{"passed":sum(r[v]["passed"] for r in rows if tag in r["tags"]),"total":sum(tag in r["tags"] for r in rows)} for v in ("v1","v2")} for tag in ("protocol","tools","correctness","safety","recovery")}
    result={"id":uuid.uuid4().hex[:12],"created_at":datetime.now(timezone.utc).isoformat(),"provider":provider.name,
        "dataset_version":data["version"],"fingerprint":data["fingerprint"],"runtime":"Python "+platform.python_version(),
        "duration_ms":round((time.perf_counter()-started)*1000,2),"total":len(rows),"passed":counts,
        "score":{v:round(counts[v]/len(rows)*100,1) for v in counts},"dimensions":dimensions,"rows":rows,
        "limitations":["确定性回放验证编排、协议和工具边界，不衡量大模型语义能力。" if provider_name=="replay" else "真实模型输出会波动；回放专用的故障注入用例不保证由在线模型触发，勿与回放成绩比较。", "语义 Judge 需单独运行；人工校准尚未提交，不声称已通过。", "memory 用例验证显式上下文输入隔离，未实现多用户持久化会话。"]}
    RESULTS.mkdir(exist_ok=True)
    serialized=json.dumps(result,ensure_ascii=False,indent=2)
    (RESULTS/(result["id"]+".json")).write_text(serialized,encoding="utf-8")
    (RESULTS/"latest.json").write_text(serialized,encoding="utf-8")
    return result


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--provider",choices=["replay","qwen"],default="replay")
    result=asyncio.run(evaluate(parser.parse_args().provider))
    print(json.dumps({k:result[k] for k in ("id","provider","fingerprint","total","passed","score","duration_ms","limitations")},ensure_ascii=False,indent=2))
