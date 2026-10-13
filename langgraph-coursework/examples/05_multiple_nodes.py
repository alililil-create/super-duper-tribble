"""模块五：分别演示字符串覆盖和图片中列表追加，多节点逐步输出。"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from state_model import State

class SimpleState(TypedDict):
    message: str

def build_overwrite_graph():
    builder = StateGraph(SimpleState)
    builder.add_node("hello", lambda state: {"message": "Hello LangGraph!"})
    builder.add_node("goodbye", lambda state: {"message": "Goodbye!"})
    builder.add_edge(START, "hello")
    builder.add_edge("hello", "goodbye")
    builder.add_edge("goodbye", END)
    return builder.compile()

def hello_node(state: State):
    return {"message": ["Hello LangGraph!"], "results": "Hello LangGraph!"}

def process_node(state: State):
    return {"message": [f"处理节点收到：{state['results']}"], "results": f"已处理用户问题：{state['user_query']}"}

def goodbye_node(state: State):
    return {"message": ["Goodbye!"], "results": "Goodbye!"}

def build_graph():
    builder = StateGraph(State)
    builder.add_node("hello", hello_node)
    builder.add_node("process", process_node)
    builder.add_node("goodbye", goodbye_node)
    builder.add_edge(START, "hello")
    builder.add_edge("hello", "process")
    builder.add_edge("process", "goodbye")
    builder.add_edge("goodbye", END)
    return builder.compile()

def main():
    print("=== 05 多个节点执行输出 ===")
    print("A. 讲义双节点：START -> hello -> goodbye -> END")
    for i, state in enumerate(build_overwrite_graph().stream({"message": ""}, stream_mode="values")):
        print(f"状态 {i}：{state}")
    print("最终 message 是 Goodbye!，后写的字符串覆盖前值。")
    print("\nB. 图片状态三节点：START -> hello -> process -> goodbye -> END")
    initial: State = {"message": [], "user_query": "学习 LangGraph", "results": ""}
    labels = ["初始", "hello 执行后", "process 执行后", "goodbye 执行后"]
    for label, state in zip(labels, build_graph().stream(initial, stream_mode="values")):
        print(f"[{label}] message={state['message']}; results={state['results']!r}")
    print("最终保留三个节点的消息；results 为 Goodbye!。")

if __name__ == "__main__":
    main()
