"""真实千问初稿与润色，MemorySaver 状态历史及可选暂停恢复。"""
import argparse
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from qwen_config import create_model

class CheckState(TypedDict):
    question: str
    draft: str
    answer: str

def build_graph(llm=None, pause=False):
    llm = llm if llm is not None else create_model()
    def draft_node(state: CheckState):
        print('[draft_node] 正在生成草稿……')
        response = llm.invoke('请用中文简要回答，150字以内，不加开场白：' + state['question'])
        return {'draft': response.content}
    def polish_node(state: CheckState):
        print('[polish_node] 正在润色草稿……')
        response = llm.invoke('请润色以下回答，使表述更准确专业，200字以内，只输出润色后的正文。'
                              '\n原问题：' + state['question'] + '\n草稿：' + state['draft'])
        return {'answer': response.content}
    graph = StateGraph(CheckState)
    graph.add_node('draft_node', draft_node)
    graph.add_node('polish_node', polish_node)
    graph.add_edge(START, 'draft_node')
    graph.add_edge('draft_node', 'polish_node')
    graph.add_edge('polish_node', END)
    return graph.compile(checkpointer=InMemorySaver(),
                         interrupt_before=['polish_node'] if pause else None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pause', action='store_true', help='在润色前暂停，再从同一存档继续')
    parser.add_argument('--question', default='什么是微积分？')
    args = parser.parse_args()
    compiled_graph = build_graph(pause=args.pause)
    config = {'configurable': {'thread_id': 'calculus-demo'}}
    result = compiled_graph.invoke({'question': args.question}, config=config)
    if args.pause:
        snapshot = compiled_graph.get_state(config)
        print('\n=== 已在润色前暂停 ===')
        print('当前状态：', snapshot.values)
        print('待执行节点：', snapshot.next)
        print('使用 invoke(None, config) 从同一检查点继续。')
        result = compiled_graph.invoke(None, config=config)
    print('\n=== 最终结果 ===')
    print('问题：', result['question'])
    print('草稿：', result['draft'])
    print('答案：', result['answer'])
    print('\n=== 执行历史（最新到最早）===')
    history = list(compiled_graph.get_state_history(config))
    print(f'共有 {len(history)} 个历史状态（包含框架的输入检查点）')
    for i, state in enumerate(history):
        print(f'状态 {i}: {state.values}')
        print(f'  待执行节点：{state.next}')
    print('\n说明：内存存档只在当前进程存活期间有效。')

if __name__ == '__main__':
    main()
