"""人机交互：千问生成SQL -> interrupt审批 -> 执行教学数据库查询。"""
import argparse
from advanced_graphs import build_review, config
from langgraph.types import Command

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--decision',choices=['yes','no'],help='仅用于可重复验证；省略则由你在终端输入')
    args=parser.parse_args()
    graph=build_review()
    cfg=config('sql-review')
    result=graph.invoke({'question':'查询年龄大于18岁的用户姓名和年龄'},cfg)
    print('图已暂停：',result['__interrupt__'][0].value)
    decision=args.decision
    if decision is None:
        decision=input('人工审批 yes/no：').strip().lower()
    else:
        print('命令行测试审批输入：',decision)
    result=graph.invoke(Command(resume=decision),cfg)
    print(result['result'])

if __name__=='__main__': main()

