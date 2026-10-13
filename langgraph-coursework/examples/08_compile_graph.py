"""图片一：注册两个节点、连接边、编译并运行；补充三种运行方式。"""
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    message: str
    output: str

def add_output(state: State):
    result = state['message'] + '，欢迎学习 LangGraph！'
    print('[add_info] 写入 output：' + result)
    return {'output': result}

def print_output(state: State):
    print('[print_info] 读取 output：' + state['output'])
    return {}  # 打印节点不修改状态；仍返回合法的部分更新

def build_graph():
    graph = StateGraph(State)
    graph.add_node('add_info', add_output)
    graph.add_node('print_info', print_output)
    graph.add_edge(START, 'add_info')
    graph.add_edge('add_info', 'print_info')
    graph.add_edge('print_info', END)
    compiled_graph = graph.compile()
    return compiled_graph

async def async_demo(graph, initial):
    print('\n=== ainvoke：异步返回最终状态 ===')
    print(await graph.ainvoke(initial))
    print('\n=== astream：按节点输出更新 ===')
    async for update in graph.astream(initial, stream_mode='updates'):
        print('节点更新：', update)

def main():
    graph = build_graph()
    print('编译成功：START -> add_info -> print_info -> END')
    initial = {'message': '你好', 'output': ''}
    print('\n=== invoke：同步返回最终状态 ===')
    print('初始状态：', initial)
    print('最终状态：', graph.invoke(initial))
    asyncio.run(async_demo(graph, initial))

if __name__ == '__main__':
    main()
