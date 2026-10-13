"""模块三：自然语言解释图结构，同时运行对应的真实图。"""
from langgraph.graph import StateGraph, START, END
from state_model import State

def analyze_node(state: State):
    query = state["user_query"].strip()
    return {"message": [f"分析节点：读到用户输入 {query!r}"], "results": query}

def generate_node(state: State):
    return {"message": ["生成节点：读取分析结果并转为大写"], "results": state["results"].upper()}

def build_graph():
    builder = StateGraph(State)
    builder.add_node("analyze", analyze_node)
    builder.add_node("generate", generate_node)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "generate")
    builder.add_edge("generate", END)
    return builder.compile()

def main():
    print("=== 03 用自然语言描述 StateGraph 结构 ===")
    print("业务：用户输入文字，先去除首尾空格，再转换成大写。")
    print("状态：user_query 保存原始输入；message 累积过程；results 保存结果。")
    print("节点：analyze 处理输入，generate 读取上一步结果并加工。")
    print("边：START -> analyze -> generate -> END，依次执行。")
    print("三步：构建节点和边 -> compile 编译 -> invoke 调用。")
    final = build_graph().invoke({"message": [], "user_query": "  hello StateGraph  ", "results": ""})
    for message in final["message"]:
        print(message)
    print("最终结果：", final["results"])

if __name__ == "__main__":
    main()
