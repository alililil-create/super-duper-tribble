"""课堂练习：GET 参数、Pydantic 数据模型及内存商品接口。"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Git 与 FastAPI 课堂作业")


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False


# 与视频一样使用内存列表，重启服务后恢复初始数据。
fake_db = [
    {"id": 1, "name": "苹果", "price": 5.0, "is_offer": False},
    {"id": 2, "name": "香蕉", "price": 3.0, "is_offer": False},
]


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/item")
def read_query_item(item_id: int):
    return {"item_id": item_id}


@app.get("/item2/{item_id}")
def read_path_item(item_id: int):
    return {"item_id": item_id}


@app.post("/item3", response_model=Item)
def transform_item(item: Item):
    """视频中的模型演示：返回价格加 1000 后的新对象，不保存。"""
    return Item(name=item.name, price=item.price + 1000, is_offer=item.is_offer)


@app.get("/items/{item_id}")
def get_one_item(item_id: int):
    for item in fake_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="商品不存在")


@app.post("/items")
def create_item(item: Item):
    new_item = {"id": max((row["id"] for row in fake_db), default=0) + 1, **item.model_dump()}
    fake_db.append(new_item)
    return {"message": "新增成功", "item": new_item}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    for row in fake_db:
        if row["id"] == item_id:
            row.update(item.model_dump())
            return {"message": "修改成功", "item": row}
    raise HTTPException(status_code=404, detail="商品不存在")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
