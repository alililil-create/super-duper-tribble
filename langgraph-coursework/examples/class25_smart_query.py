"""智能问数助手：三表真实查询，支持自定义问题。"""
import argparse
from smart_query_core import init_database, schema_text, build_query, china_today, month_bounds

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--question')
    args=parser.parse_args()
    today=china_today(); path=init_database(today=today)
    print('数据库初始化完成，3张表：products、users、orders。')
    print('数据库：',path)
    print('当前日期：',today,'；上个月范围：',month_bounds(today))
    print('数据库结构：\n'+schema_text(path))
    graph=build_query(path,today=today)
    questions=[args.question] if args.question else [
        '上个月华北地区销售额是多少？','上个月各品类销售额是多少？','北京用户的订单总金额是多少？']
    for i,q in enumerate(questions,1):
        print(f'\n【问题{i}/{len(questions)}】{q}\n'+'='*65)
        result=graph.invoke({'question':q},{'recursion_limit':30})
        print('最终答案：\n'+result['answer'])
        print('修正次数：',result['retries'])
        if result.get('error'): raise RuntimeError(result['error'])
        if not args.question:
            expected=[[(6898.0,)], [('家电',798.0),('数码产品',35995.0),('服装',1798.0),('食品',1592.0)], [(7297.0,)]]
            if sorted(result['rows'])!=sorted(expected[i-1]):
                raise RuntimeError('示例结果与基准数据不符，请检查生成SQL的筛选条件。')
            print('[核对] 与示例数据基准结果一致')

if __name__=='__main__': main()
