import asyncio
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.evaluation import ROOT, RESULTS, evaluate, load_dataset
from app.design import designs

app=FastAPI(title="商城智能体测评中心",version="1.0.0",description="课程本地沙箱：10.20 测评体系 / 10.22 改造设计")
lock=asyncio.Lock()

@app.get("/health")
def health():
    return {"status":"ok","service":"shop-agent-lab"}

@app.get("/api/datasets")
def datasets():
    return load_dataset()

@app.get("/api/designs")
def design_list():
    return designs()

@app.get("/api/results/latest")
def latest():
    path=RESULTS/"latest.json"
    if not path.exists():
        raise HTTPException(404,"尚未运行测评")
    return json.loads(path.read_text(encoding="utf-8"))

@app.post("/api/evaluations")
async def evaluation():
    # Browser only triggers free, bounded local replay. Paid online runs are explicit CLI operations.
    if lock.locked():
        raise HTTPException(409,"已有测评正在运行")
    async with lock:
        return await evaluate("replay")

@app.get("/")
def index():
    return FileResponse(ROOT/"web/index.html")

app.mount("/static",StaticFiles(directory=ROOT/"web"),name="static")
