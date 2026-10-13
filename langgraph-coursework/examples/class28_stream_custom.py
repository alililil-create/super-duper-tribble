from stream_subgraph_core import build_custom
def main():
    print("自定义流式输出：stream_mode='custom'\n问题：什么是人工智能？\nAI回复：")
    count=0
    for event in build_custom().stream({'question':'什么是人工智能？'},stream_mode='custom'):
        if event['type']=='status': print('[状态] '+event['text'],flush=True)
        elif event['type']=='token':
            print(event['text'],end='',flush=True); count+=1
        else: print('\n[状态] 输出完成',flush=True)
    print('实际接收文本块数量：',count)
if __name__=='__main__': main()
