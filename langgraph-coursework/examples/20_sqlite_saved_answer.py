"""第一次真实问答存档，再次启动只读取SQLite，不重新调用Qwen。"""
import argparse
from langgraph.checkpoint.sqlite import SqliteSaver
from advanced_graphs import ROOT, build_checkpoints, config

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--thread',default='python-java')
    parser.add_argument('--question',default='Python和Java有什么区别？')
    args=parser.parse_args()
    folder=ROOT/'data'; folder.mkdir(exist_ok=True)
    with SqliteSaver.from_conn_string(str(folder/'saved_answers.sqlite')) as saver:
        # 读档时不创建或请求模型；只有process节点实际执行才延迟初始化。
        class LazyModel:
            def invoke(self,*a,**kw):
                from qwen_config import create_model
                return create_model().invoke(*a,**kw)
        graph=build_checkpoints(LazyModel(),saver=saver)
        cfg=config(args.thread)
        saved=graph.get_state(cfg).values
        if saved.get('final_output'):
            print('[检测到历史存档] 从SQLite文件恢复之前的状态：')
            print('上次输入：',saved['user_input'])
            print('上次结果：',saved['final_output'])
            print('无需重新调用Qwen，直接从存档读取结果！')
        else:
            result=graph.invoke({'user_input':args.question},cfg)
            print('第一次执行结果：',result['final_output'])
            print('已保存；再次运行同一命令即可读档。')
    print('切换问题请使用新的 --thread，已有会话保留原结果。')

if __name__=='__main__': main()
