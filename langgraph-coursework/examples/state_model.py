"""图片里的状态结构。注意 message 是列表，不是原图注释所说的字符串。"""
from operator import add
from typing import Annotated, TypedDict

class State(TypedDict):
    message: Annotated[list[str], add]  # 节点返回的新消息由图自动追加
    user_query: str                    # 用户原始问题
    results: str                       # 结果字段；顺序写入时后值覆盖前值

class WeatherState(TypedDict):
    """讲义状态设计练习，仅定义结构，不编造天气查询结果。"""
    messages: Annotated[list[str], add]
    user_query: str
    city: str
    query_date: str
    weather_info: str
    final_answer: str
