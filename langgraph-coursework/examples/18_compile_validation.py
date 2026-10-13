"""真实编译、运行五种图结构，不仅打印结构说明。"""
from operator import add
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    message: str
    outputs: Annotated[list[str],add]
    count: int

def build_case(kind):
    b=StateGraph(State)
    if kind=='loop':
        b.add_node('a',lambda s:{'count':s['count']+1})
        b.add_node('b',lambda s:{})
        b.add_node('c',lambda s:{})
        b.add_edge(START,'a'); b.add_edge('a','b'); b.add_edge('b','c')
        b.add_conditional_edges('c',lambda s:'end' if s['count']>=2 else 'a',{'end':END,'a':'a'})
    else:
        b.add_node('a',lambda s:{'message':'A'})
        b.add_node('b',lambda s:{'outputs':['B']} if kind=='branch' else {'message':'B'})
        b.add_edge(START,'a')
        if kind=='isolated': b.add_edge('a',END)
        else: b.add_edge('a','b')
        if kind in ('normal','branch'): b.add_edge('b',END)
        if kind=='disconnected':
            b.add_node('c',lambda s:{'message':'C'})
            b.add_node('d',lambda s:{'message':'D'})
            b.add_edge('c','d'); b.add_edge('d',END)
        if kind=='branch':
            b.add_node('c',lambda s:{'outputs':['C']})
            b.add_edge('a','c'); b.add_edge('c',END)
    return b.compile()

def main():
    cases=[('normal','正常连接：START -> a -> b -> END'),
           ('isolated','孤立节点：START -> a -> END；b已注册但没有边'),
           ('disconnected','断开的连接：START -> a -> b；c -> d -> END从START不可达'),
           ('branch','分支：a -> b/c -> END；列表通过reducer合并'),
           ('loop','循环：a -> b -> c -> a；计数到2后结束')]
    for kind,title in cases:
        print('\n'+'-'*65+'\n'+title)
        initial={'count':0} if kind=='loop' else {}
        result=build_case(kind).invoke(initial,{'recursion_limit':20})
        print('真实执行结果：',result)
    print('\n孤立节点和不可达组件在本版本中可编译，但不会执行；循环需设计退出条件。')

if __name__=='__main__': main()
