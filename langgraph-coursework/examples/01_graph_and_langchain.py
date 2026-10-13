"""模块一：用相同处理函数比较 LCEL 链和 LangGraph 有向图。"""
from typing import TypedDict
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph, START, END

def clean(text: str) -> str:
    return text.strip()

def upper(text: str) -> str:
    return text.upper()

class TextState(TypedDict):
    text: str

def build_graph():
    builder = StateGraph(TextState)
    builder.add_node("clean", lambda state: {"text": clean(state["text"])})
    builder.add_node("upper", lambda state: {"text": upper(state["text"])})
    builder.add_edge(START, "clean")
    builder.add_edge("clean", "upper")
    builder.add_edge("upper", END)
    return builder.compile()

def main():
    print("=== 01 有向图与 LangChain ===")
    print("节点完成任务，边规定方向，State 在节点之间传递数据。")
    print("有向图可有环；DAG 是有向无环图。")
    print("本例路径：START -> clean -> upper -> END")
    chain = RunnableLambda(clean) | RunnableLambda(upper)
    text = "  hello langgraph  "
    print("输入：", repr(text))
    print("LangChain LCEL 输出：", chain.invoke(text))
    print("LangGraph 输出：", build_graph().invoke({"text": text}))
    print("LCEL 适合组合处理步骤；LangGraph 显式定义状态、节点和流转。")

if __name__ == "__main__":
    main()
