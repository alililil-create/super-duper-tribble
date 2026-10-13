"""在 LangGraph 节点内真实调用千问。"""
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from state_model import State
from qwen_config import create_model

def build_graph(llm=None):
    llm = llm if llm is not None else create_model()
    def ask_qwen_node(state: State):
        print('[ask_qwen_node] 用户问题：' + state['user_query'])
        response = llm.invoke([SystemMessage(content='你是简洁的中文助手。只用一句话回答，不使用表情。'),
                               HumanMessage(content=state['user_query'])])
        answer = response.content
        print('[ask_qwen_node] 模型回答：' + answer)
        return {'message': [answer], 'results': answer}
    builder = StateGraph(State)
    builder.add_node('ask_qwen', ask_qwen_node)
    builder.add_edge(START, 'ask_qwen')
    builder.add_edge('ask_qwen', END)
    return builder.compile()

def main():
    result = build_graph().invoke({'message': [], 'user_query': '请用一句话解释什么是人工智能？', 'results': ''})
    print('\n=== 最终结果 ===')
    print('用户问题：' + result['user_query'])
    print('AI回答：' + result['results'])

if __name__ == '__main__':
    main()
