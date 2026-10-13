"""检查点：两个独立会话、当前状态和完整历史。"""
from advanced_graphs import build_checkpoints, config

def main():
    graph=build_checkpoints()
    for thread,question in [('zhangsan','用一句话解释人工智能'),('lisi','用一句话解释LangGraph')]:
        cfg=config(thread)
        graph.invoke({'user_input':question},cfg)
        print('\n会话：',thread)
        print('当前状态：',graph.get_state(cfg).values)
        for i,snapshot in enumerate(graph.get_state_history(cfg)):
            print(f'历史 {i}：{snapshot.values}；待执行：{snapshot.next}')
    assert graph.get_state(config('zhangsan')).values['user_input']=='用一句话解释人工智能'
    assert not graph.get_state(config('unknown')).values
    print('\n会话隔离验证通过，内存检查点在进程关闭后失效。')

if __name__=='__main__': main()

