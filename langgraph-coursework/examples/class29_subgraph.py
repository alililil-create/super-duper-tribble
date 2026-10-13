from stream_subgraph_core import build_article
def main():
    print('子图设计演示\n父图：START -> subgraph -> END\n子图：START -> title -> article -> END')
    print('[父图] 主题：人工智能的起源\n[父图] 调用子图……')
    result=build_article().invoke({'topic':'人工智能的起源'})
    print('[父图] 收到子图结果，执行完毕\n最终状态：')
    for key,value in result.items(): print(key+': '+value)
if __name__=='__main__': main()
