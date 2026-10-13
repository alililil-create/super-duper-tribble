"""智能客服改造：回复草稿交由人工审核，拒绝则不采用。"""
import argparse
from advanced_graphs import build_service, config
from uuid import uuid4
from langgraph.types import Command

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--decision',choices=['yes','no'])
    args=parser.parse_args()
    graph=build_service(human_review=True)
    cfg=config('customer-review')
    result=graph.invoke({'user_input':'我要投诉，昨天收到的手机屏幕有划痕。','attempts':0,
                         'path':[],'complaint_log':[],'ticket_id':'LOCAL-'+uuid4().hex[:12]},cfg)
    while result.get('__interrupt__'):
        print('客服回复待审核：',result['__interrupt__'][0].value)
        decision=args.decision
        if decision is None: decision=input('人工审核 yes/no：').strip().lower()
        else: print('命令行测试审核输入：',decision)
        result=graph.invoke(Command(resume=decision),cfg)
    print('审核状态：','approved' if result.get('approved') else 'rejected')
    print('最终状态：',result['status'])
    print('重试次数：',result['attempts']-1)
    if result.get('approved'): print('审核通过回复：',result['response'])
    else: print('回复未通过审核，已记录为待人工处理。')
    for entry in result['complaint_log']: print(entry)
    print('实际节点：',' -> '.join(result['path']))

if __name__=='__main__': main()

