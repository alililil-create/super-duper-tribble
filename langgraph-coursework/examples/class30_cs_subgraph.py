from stream_subgraph_core import build_customer_subgraph
def main():
    print('智能客服系统（含投诉处理子图）测试')
    graph=build_customer_subgraph()
    for question in ['我要投诉，昨天买的手机屏幕有划痕','请问你们的退货政策是怎样的？']:
        print('\n'+'='*60+'\n用户问题：'+question)
        result=graph.invoke({'user_message':question})
        print('意图：',result['intent'])
        if result.get('complaint_type'): print('投诉类型：',result['complaint_type'])
        print('回复：',result['reply'])
if __name__=='__main__': main()
