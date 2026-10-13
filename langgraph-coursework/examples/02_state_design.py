"""模块二：在真正的 StateGraph 中验证追加与覆盖规则。"""
from langgraph.graph import StateGraph, START, END
from state_model import State

def first_node(state: State):
    return {"message": ["你好，我是 AI 助手"], "results": "节点一完成"}

def second_node(state: State):
    return {"message": ["请问有什么可以帮助你？"], "results": "节点二完成"}

def build_graph():
    builder = StateGraph(State)
    builder.add_node("first", first_node)
    builder.add_node("second", second_node)
    builder.add_edge(START, "first")
    builder.add_edge("first", "second")
    builder.add_edge("second", END)
    return builder.compile()

def main():
    print("=== 02 状态设计 ===")
    print("class State(TypedDict):")
    print("    message: Annotated[list[str], add]")
    print("    user_query: str")
    print("    results: str")
    initial: State = {"message": [], "user_query": "测试状态合并", "results": ""}
    for i, snapshot in enumerate(build_graph().stream(initial, stream_mode="values")):
        print(f"状态快照 {i}：{snapshot}")
    print("message 追加两条消息；results 被第二个值覆盖；user_query 保留。")
    print("注意：TypedDict 负责类型描述，不负责运行时自动校验。")

if __name__ == "__main__":
    main()
