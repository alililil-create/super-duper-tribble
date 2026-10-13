"""循环写诗与检查；最多生成三次，不合格不会假称成功。"""
from advanced_graphs import build_loop

def main():
    graph=build_loop()
    for topic in ['月亮','春天','代码']:
        print('\n'+'='*50+'\n主题：'+topic)
        result=graph.invoke({'topic':topic,'attempts':0},{'recursion_limit':20})
        print('\n生成次数：',result['attempts'],'；重试次数：',result['attempts']-1)
        print('最终质量：',result['quality'])
        if result['quality']!='合格': print('已达次数上限，需要人工修改。')
        print(result['poem'])

if __name__=='__main__': main()

