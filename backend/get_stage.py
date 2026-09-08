"""GET 视频对应的阶段代码，最终版本见 main.py。"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/item")
def read_query_item(item_id: int):
    return {"item_id": item_id}


@app.get("/item2/{item_id}")
def read_path_item(item_id: int):
    return {"item_id": item_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
