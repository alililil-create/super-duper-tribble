"""SQLite持久化：先start关闭进程，再resume恢复审批，show只读查看。"""
import argparse
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from advanced_graphs import ROOT, build_review, config

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['start','resume','show'],nargs='?',default='show')
    parser.add_argument('--thread',default='sqlite-homework')
    parser.add_argument('--decision',choices=['yes','no'])
    parser.add_argument('--db',default=str(ROOT/'data'/'checkpoints.sqlite'))
    args=parser.parse_args()
    from pathlib import Path
    db=Path(args.db).resolve()
    if db.drive.lower()!='d:': raise ValueError('请把数据库放在D盘')
    db.parent.mkdir(parents=True,exist_ok=True)
    with SqliteSaver.from_conn_string(str(db)) as saver:
        graph=build_review(saver=saver)
        cfg=config(args.thread)
        snapshot=graph.get_state(cfg)
        if args.action=='start':
            if snapshot.values: raise ValueError('此会话已存在，请用resume/show或更换--thread')
            result=graph.invoke({'question':'查询年龄大于18岁的用户姓名和年龄'},cfg)
            print('已保存暂停检查点：',result['__interrupt__'][0].value)
            print('进程可以关闭。下次使用相同 --thread 执行 resume。')
        elif args.action=='resume':
            if not snapshot.next: raise ValueError('没有待恢复节点，请先start或使用正确thread')
            print('从磁盘恢复，已有草稿：',snapshot.values['draft'])
            decision=args.decision
            if decision is None: decision=input('人工审批 yes/no：').strip().lower()
            else: print('命令行测试审批输入：',decision)
            print(graph.invoke(Command(resume=decision),cfg)['result'])
        else:
            print('当前磁盘存档：',snapshot.values)
            print('待执行节点：',snapshot.next)
        print('数据库：',db)

if __name__=='__main__': main()

