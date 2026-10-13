"""智能问答路由：按复杂度选择简洁或详细回答，日期由本机时钟提供。"""
from datetime import datetime, timezone, timedelta
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from advanced_graphs import ask, choice
from qwen_config import create_model

class State(TypedDict):
    question: str
    complexity: str
    answer: str

def build_graph(llm=None):
    llm=llm if llm is not None else create_model()
    def analyze(s):
        print('[analyze_intent] 正在分析问题复杂度……')
        return {'complexity':choice(llm,'简单事实或定义为简单；需要分析过程、比较或举例为复杂。',s['question'],['简单','复杂'])}
    def answer(detailed):
        def run(s):
            print('[detailed_answer] 生成详细回答……' if detailed else '[simple_answer] 生成简洁回答……')
            today=datetime.now(timezone(timedelta(hours=8)))
            date=today.strftime('%Y年%m月%d日')+'，星期'+'一二三四五六日'[today.weekday()]
            prompt=('分步骤解释并举例，350字以内。不要把Python的sorted称为快速排序实现，它使用Timsort。'
                    '快速排序的递归栈平均O(log n)，最坏O(n)。' if detailed else '简洁回答，80字以内。')
            if any(word in s['question'] for word in ['今天','日期','星期']):
                prompt+=' 当前北京时间日期为'+date+'。询问今天时必须依据此日期。'
            return {'answer':ask(llm,prompt,s['question'])}
        return run
    b=StateGraph(State)
    b.add_node('analyze_intent',analyze)
    b.add_node('simple_answer',answer(False)); b.add_node('detailed_answer',answer(True))
    b.add_edge(START,'analyze_intent')
    b.add_conditional_edges('analyze_intent',lambda s:s['complexity'],{'简单':'simple_answer','复杂':'detailed_answer'})
    b.add_edge('simple_answer',END); b.add_edge('detailed_answer',END)
    return b.compile()

def main():
    print('='*60+'\n智能问答路由器\n'+'='*60)
    graph=build_graph()
    for i,q in enumerate(['今天星期几？','什么是变量？','请解释快速排序的工作原理，并举一个实际应用例子'],1):
        print(f'\n测试 {i}：{q}')
        result=graph.invoke({'question':q})
        print('复杂度：',result['complexity']); print('答案：',result['answer'])

if __name__=='__main__': main()
