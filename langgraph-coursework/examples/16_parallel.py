"""Send动态并行：三个主题真实请求千问，列表合并并按输入顺序输出。"""
from advanced_graphs import build_parallel

def main():
    result=build_parallel(synthesize=True).invoke({'topics':['人工智能','区块链','量子计算'],'results':[]},{'max_concurrency':3})
    for item in sorted(result['results'],key=lambda x:x['index']):
        print(f"\n【文章 {item['index']+1}】{item['topic']}：{item['content']}")
    print('\n综合摘要：\n'+result['summary'])
    records=result['results']
    overlap=any(a['started']<b['ended'] and b['started']<a['ended'] for i,a in enumerate(records) for b in records[i+1:])
    print('实际任务时间区间存在重叠：',overlap)
    for item in records: print(item['topic'],f"耗时 {item['ended']-item['started']:.2f} 秒")
    assert len(records)==3

if __name__=='__main__': main()

