"""真实SQLite问数图：关键词、Schema、生成、数据库验证、执行、错误修正。"""
import json
import re
import sqlite3
import time
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from advanced_graphs import ROOT, ask
from qwen_config import create_model

def china_today():
    return datetime.now(timezone(timedelta(hours=8))).date()

def month_bounds(today):
    end=today.replace(day=1)
    return (end-timedelta(days=1)).replace(day=1),end

def init_database(folder=None, today=None):
    today=today or china_today()
    start,end=month_bounds(today)
    folder=Path(folder) if folder else ROOT/'data'
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/f'ecommerce_demo_{start:%Y%m}.sqlite'
    # 仅新建独立教学库；重复运行不清空已有数据。
    with closing(sqlite3.connect(path)) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS products(product_id INTEGER PRIMARY KEY,product_name TEXT,category TEXT,price REAL);
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,user_name TEXT,gender TEXT,age INTEGER,city TEXT);
        CREATE TABLE IF NOT EXISTS orders(order_id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(user_id),
          product_id INTEGER REFERENCES products(product_id),quantity INTEGER,amount REAL,order_date TEXT,region TEXT);
        ''')
        if not conn.execute('SELECT count(*) FROM products').fetchone()[0]:
            conn.executemany('INSERT INTO products VALUES(?,?,?,?)',[
                (2001,'华为MateBook','数码产品',5999),(2002,'iPhone15','数码产品',7999),
                (2003,'三只松鼠礼盒','食品',199),(2004,'耐克运动鞋','服装',899),(2005,'美的电饭煲','家电',399)])
            conn.executemany('INSERT INTO users VALUES(?,?,?,?,?)',[
                (1001,'张三','男',28,'北京'),(1002,'李四','男',35,'上海'),(1003,'王五','女',22,'广州'),
                (1004,'赵六','女',30,'深圳'),(1005,'孙七','男',45,'杭州')])
            base=[(3001,1001,2001,1,5999,1,'华北'),(3002,1002,2002,2,15998,3,'华东'),
                  (3003,1003,2003,3,597,5,'华南'),(3004,1001,2004,1,899,8,'华北'),
                  (3005,1004,2001,1,5999,10,'华南'),(3006,1005,2005,2,798,12,'华东'),
                  (3007,1002,2003,5,995,15,'华东'),(3008,1003,2004,1,899,18,'华南'),
                  (3009,1005,2002,1,7999,20,'华东')]
            conn.executemany('INSERT INTO orders VALUES(?,?,?,?,?,?,?)',
                [(*r[:5],start.replace(day=r[5]).isoformat(),r[6]) for r in base]+
                [(3010,1001,2005,1,399,end.replace(day=2).isoformat(),'华北')])
            conn.commit()
    return path

def schema_text(path):
    with closing(sqlite3.connect(path)) as conn:
        lines=[]
        for table in ('products','users','orders'):
            lines.append('[表 '+table+']')
            lines.extend('  '+r[1]+' '+r[2] for r in conn.execute('PRAGMA table_info('+table+')'))
    return '\n'.join(lines)+'\n关联：orders.user_id=users.user_id；orders.product_id=products.product_id。城市在users.city，地区在orders.region。'

def clean_sql(text):
    return re.sub(r'^```(?:sql)?\s*|\s*```$','',text.strip(),flags=re.I).strip()

def read_query(path,sql,validate=False):
    if len(sql)>12000 or not re.match(r'^SELECT\b',sql,re.I):
        raise ValueError('只允许一条SELECT查询')
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as conn:
        conn.execute('PRAGMA query_only=ON')
        tables={'products','users','orders'}
        functions={'sum','count','avg','min','max','round','coalesce','ifnull','date','strftime','lower','upper','abs'}
        def authorize(action,a,b,db,trigger):
            ok=(action==sqlite3.SQLITE_SELECT or
                action==sqlite3.SQLITE_READ and a in tables or
                action==sqlite3.SQLITE_FUNCTION and b.lower() in functions)
            return sqlite3.SQLITE_OK if ok else sqlite3.SQLITE_DENY
        conn.set_authorizer(authorize)
        deadline=time.monotonic()+3
        conn.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
        cursor=conn.execute(('EXPLAIN QUERY PLAN ' if validate else '')+sql)
        rows=cursor.fetchmany(201)
        return [d[0] for d in cursor.description],rows[:200],len(rows)>200

class QueryState(TypedDict):
    question: str
    keywords: dict
    schema: str
    sql: str
    error: str
    retries: int
    columns: list[str]
    rows: list
    truncated: bool
    answer: str

def build_query(path,llm=None,today=None):
    llm=llm if llm is not None else create_model()
    today=today or china_today()
    start,end=month_bounds(today)
    full_schema=schema_text(path)
    def keywords(s):
        text=ask(llm,'提取查询关键词，只输出JSON对象，字段tables,columns,conditions,metrics均为列表。'
                 f'今天{today}，上个月范围{start}至{end}（不含后者）。华北/华东/华南是orders.region，'
                 '北京/上海等城市是users.city。只能使用下列真实字段，不可猜测字段。\n'+full_schema,s['question'])
        data=json.loads(clean_sql(text).removeprefix('json').strip())
        if not isinstance(data,dict) or any(not isinstance(data.get(k),list) for k in ('tables','columns','conditions','metrics')):
            raise ValueError('关键词JSON格式不正确')
        print('[关键词]',json.dumps(data,ensure_ascii=False))
        return {'keywords':data,'retries':0,'error':''}
    def schema(s):
        # 三张小表全部提供，避免漏掉JOIN依赖表。
        return {'schema':full_schema}
    def generate(s):
        instruction=('只生成一条SQLite SELECT，不要解释。不得修改数据或使用外部函数。金额使用amount。'
                     f'当前日期{today}；上个月范围 >= {start} 且 < {end}。城市条件必须关联users。'
                     '华北、华东、华南等大区仅使用orders.region过滤，绝不能用users.city。'
                     '关键词仅辅助，若与真实Schema或用户问题冲突，请以Schema和用户问题为准。\n'+s['schema'])
        context=s['question']+'\n关键词：'+json.dumps(s['keywords'],ensure_ascii=False)
        if s.get('error'): context+='\n请修正原SQL：'+s['sql']+'\n错误：'+s['error']
        sql=clean_sql(ask(llm,instruction,context))
        print('[生成SQL]',sql)
        return {'sql':sql,'error':''}
    def validate(s):
        try:
            read_query(path,s['sql'],validate=True)
            print('[验证] SQLite语法和字段检查通过')
            return {'error':''}
        except (sqlite3.Error,ValueError) as e:
            print('[验证失败]',str(e)); return {'error':str(e)}
    def execute(s):
        try:
            columns,rows,truncated=read_query(path,s['sql'])
            print('[真实查询结果]',rows)
            return {'columns':columns,'rows':rows,'truncated':truncated,'error':''}
        except (sqlite3.Error,ValueError) as e: return {'error':str(e)}
    def fix(s):
        print('[修正] 第',s['retries']+1,'次')
        return {'retries':s['retries']+1}
    def format_result(s):
        if s.get('error'): return {'answer':'查询失败，已达到修正上限：'+s['error']}
        if not s['rows']: return {'answer':'未找到符合条件的数据。'}
        text=' | '.join(s['columns'])+'\n'+'\n'.join(' | '.join('NULL' if v is None else str(v) for v in row) for row in s['rows'])
        return {'answer':text+('\n结果超过200行，仅展示前200行。' if s['truncated'] else '')}
    def after_validation(s): return ('fix' if s['retries']<3 else 'format') if s['error'] else 'execute'
    def after_execute(s): return ('fix' if s['retries']<3 else 'format') if s['error'] else 'format'
    b=StateGraph(QueryState)
    for name,fn in [('keywords',keywords),('schema',schema),('generate',generate),('validate',validate),('execute',execute),('fix',fix),('format',format_result)]: b.add_node(name,fn)
    b.add_edge(START,'keywords'); b.add_edge('keywords','schema'); b.add_edge('schema','generate')
    b.add_edge('generate','validate'); b.add_conditional_edges('validate',after_validation,['fix','format','execute'])
    b.add_conditional_edges('execute',after_execute,['fix','format']); b.add_edge('fix','generate'); b.add_edge('format',END)
    return b.compile()
