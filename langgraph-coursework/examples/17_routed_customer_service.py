"""综合客服：三类路由、投诉并行处理、质量检查循环与本地转人工。"""
import json
from uuid import uuid4
from advanced_graphs import ROOT, build_service

def main():
    graph=build_service()
    records=[]
    for text in ['衣服尺码不合适，我想退货退款。','请问下单前在哪里查看发货时间？','我要投诉，你们的客服态度很差。']:
        print('\n'+'='*55+'\n用户：'+text)
        result=graph.invoke({'user_input':text,'attempts':0,'complaint_log':[],'path':[],
                             'ticket_id':'LOCAL-'+uuid4().hex[:12]},{'recursion_limit':60})
        print('回复：',result['response'])
        print('状态：',result['status'])
        print('处理次数：',result['attempts'])
        print('实际节点：',' -> '.join(result['path']))
        for entry in result['complaint_log']: print(entry)
        records.append(result)
    folder=ROOT/'data'; folder.mkdir(exist_ok=True)
    target=folder/('customer-service-'+uuid4().hex[:8]+'.json')
    target.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print('\n本地作业记录：',target)
    print('主管通知仅为待发送草稿，未发送外部消息；工单和转人工均为本地记录。')

if __name__=='__main__': main()

