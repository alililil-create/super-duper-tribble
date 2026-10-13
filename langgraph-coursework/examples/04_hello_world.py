"""模块四：讲义中的单节点 Hello World 图，无需调用大模型。"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class HelloState(TypedDict):
    message: str

def hello_node(state: HelloState):
    return {"message": "Hello LangGraph!"}

def build_graph():
    builder = StateGraph(HelloState)
    builder.add_node("hello", hello_node)
    builder.add_edge(START, "hello")
    builder.add_edge("hello", END)
    return builder.compile()

def main():
    print("=== 04 第一个 LangGraph 图：Hello World ===")
    print("执行路径：START -> hello -> END")
    initial: HelloState = {"message": ""}
    result = build_graph().invoke(initial)
    print("初始 State：", initial)
    print("最终 State：", result)
    print("message 字段：", result["message"])

if __name__ == "__main__":
    main()
