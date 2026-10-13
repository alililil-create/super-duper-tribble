"""三条条件边：问候、知识问答、计算。"""
from advanced_graphs import build_conditional

def main():
    graph=build_conditional()
    for text in ['你好呀','地球到月球平均有多远？','计算25×4+100等于多少']:
        print('\n用户输入：',text)
        result=graph.invoke({'user_input':text,'path':[]})
        print('实际路径：',' -> '.join(result['path']))
        print('回复：',result['response'])

if __name__=='__main__': main()

