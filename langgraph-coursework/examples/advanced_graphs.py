"""模块五、六的图定义。模型可注入以测试控制流，命令行示例使用真实千问。"""
import json
import operator
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Send
from qwen_config import create_model

ROOT = Path(__file__).resolve().parents[1]

def ask(llm, instruction, text):
    response = llm.invoke([SystemMessage(content=instruction), HumanMessage(content=text)])
    if not isinstance(response.content, str) or not response.content.strip():
        raise ValueError('模型未返回有效文本')
    return response.content.strip()

def choice(llm, instruction, text, allowed):
    value = ask(llm, instruction + ' 只返回一个标签：' + ', '.join(allowed), text)
    if value not in allowed:
        raise ValueError('模型返回了未知标签：' + value)
    return value

def config(thread):
    return {'configurable': {'thread_id': thread}, 'recursion_limit': 60}

class ReviewState(TypedDict):
    question: str
    draft: str
    approved: bool
    result: str

def build_review(llm=None, customer=False, saver=None):
    """生成与审批分开：恢复 interrupt 时不重复生成，拒绝时不执行。"""
    llm = llm if llm is not None else create_model()
    def generate(s):
        print('[generate] 调用千问生成' + ('客服回复' if customer else 'SQL'))
        instruction = ('你是客服，针对投诉礼貌回复，80字以内；不要声称已经退款或通知他人。'
                       if customer else
                       '根据问题只输出一条SQLite SELECT语句，不要代码围栏。'
                       '仅有users(id INTEGER,name TEXT,age INTEGER)表。')
        return {'draft': ask(llm, instruction, s['question'])}
    def review(s):
        decision = interrupt({'待审核内容': s['draft'], '提示': '输入 yes 同意 / no 拒绝'})
        if decision not in ('yes', 'no'):
            raise ValueError('审批只接受 yes 或 no')
        return {'approved': decision == 'yes'}
    def execute(s):
        if not s['approved']:
            return {'result': '审核拒绝，未执行SQL或采用客服回复。'}
        if customer:
            return {'result': '审核通过的客服回复：' + s['draft']}
        # 真实查询隔离的教学数据，禁止任何写操作及外部数据库访问。
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.execute('CREATE TABLE users(id INTEGER, name TEXT, age INTEGER)')
            conn.executemany('INSERT INTO users VALUES(?,?,?)', [(1,'张三',20),(2,'李四',16),(3,'王五',25)])
            conn.commit()
            allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
            conn.set_authorizer(lambda action, *args: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
            conn.set_progress_handler(lambda: 1, 100000)
            rows = conn.execute(s['draft']).fetchall()
        return {'result': '教学数据库真实查询结果：' + repr(rows)}
    b = StateGraph(ReviewState)
    for name, fn in [('generate',generate),('review',review),('execute',execute)]:
        b.add_node(name, fn)
    b.add_edge(START,'generate'); b.add_edge('generate','review')
    b.add_edge('review','execute'); b.add_edge('execute',END)
    return b.compile(checkpointer=saver if saver is not None else InMemorySaver())

class CheckState(TypedDict):
    user_input: str
    processed: str
    final_output: str

def build_checkpoints(llm=None, saver=None):
    llm = llm if llm is not None else create_model()
    def process(s):
        print('[process] 真实调用千问')
        return {'processed': ask(llm,'请用50字以内中文回答。',s['user_input'])}
    b = StateGraph(CheckState)
    b.add_node('input', lambda s: {'user_input': s['user_input'].strip()})
    b.add_node('process', process)
    b.add_node('output', lambda s: {'final_output': s['processed']})
    b.add_edge(START,'input'); b.add_edge('input','process')
    b.add_edge('process','output'); b.add_edge('output',END)
    return b.compile(checkpointer=saver if saver is not None else InMemorySaver())

class ConditionalState(TypedDict):
    user_input: str
    category: str
    response: str
    path: Annotated[list[str], operator.add]

def build_conditional(llm=None):
    llm = llm if llm is not None else create_model()
    def classify(s):
        category = choice(llm, '分类：问候greeting，知识问题question，算术calculate。',
                          s['user_input'], ['greeting','question','calculate'])
        print('[classify] 分类结果：', category)
        return {'category': category, 'path': ['classify']}
    def handler(label):
        def run(s):
            print('[' + label + '] 正在处理')
            return {'response':ask(llm,'请简短回答；算术请给出计算过程和结果。',s['user_input']), 'path':[label]}
        return run
    b = StateGraph(ConditionalState)
    b.add_node('classify', classify); b.add_edge(START,'classify')
    mapping = {'greeting':'greet','question':'answer','calculate':'calculator'}
    for name in mapping.values():
        b.add_node(name,handler(name)); b.add_edge(name,END)
    b.add_conditional_edges('classify', lambda s:s['category'],mapping)
    return b.compile()

class LoopState(TypedDict):
    topic: str
    poem: str
    attempts: int
    quality: str

def build_loop(llm=None):
    llm = llm if llm is not None else create_model()
    def generate(s):
        n = s.get('attempts',0)+1
        poem = ask(llm,'写四行中文短诗，每行不超过10个汉字，不要标题、序号或解释。',
                   '主题：'+s['topic']+'；上次检查：'+s.get('quality','首次生成'))
        print(f'[generate] 第 {n} 次生成：\n{poem}')
        return {'poem':poem,'attempts':n}
    def check(s):
        lines = [line.strip() for line in s['poem'].splitlines() if line.strip()]
        quality = choice(llm,'评估短诗是否切合主题且通顺。',s['topic']+'\n'+s['poem'],['合格','不合格'])
        if len(lines)!=4 or any(sum(c.isalnum() for c in line)>10 for line in lines):
            quality='不合格'
        print('[check] 质量：'+quality)
        return {'quality':quality}
    b = StateGraph(LoopState)
    b.add_node('generate',generate); b.add_node('check',check)
    b.add_edge(START,'generate'); b.add_edge('generate','check')
    b.add_conditional_edges('check',lambda s:'end' if s['quality']=='合格' or s['attempts']>=3 else 'retry',
                            {'end':END,'retry':'generate'})
    return b.compile()

class ParallelState(TypedDict):
    topics: list[str]
    results: Annotated[list[dict], operator.add]
    summary: str

def build_parallel(llm=None, synthesize=False):
    llm = llm if llm is not None else create_model()
    def dispatch(s):
        return [Send('write',{'topic':topic,'index':i}) for i,topic in enumerate(s['topics'])] or 'merge'
    def write(s):
        started=time.perf_counter()
        print('[write] 开始：'+s['topic'])
        content=ask(llm,'用40字以内介绍该主题。',s['topic'])
        ended=time.perf_counter()
        print('[write] 完成：'+s['topic'])
        return {'results':[dict(s,content=content,started=started,ended=ended)]}
    def merge(s):
        records=sorted(s.get('results',[]),key=lambda item:item['index'])
        articles='\n'.join(x['topic']+'：'+x['content'] for x in records)
        summary=ask(llm,'根据以下各篇文章写80字以内综合摘要，比较共同点和区别。',articles) if synthesize and records else articles
        return {'summary':summary}
    b=StateGraph(ParallelState)
    b.add_node('write',write); b.add_node('merge',merge)
    b.add_conditional_edges(START,dispatch,['write','merge'])
    b.add_edge('write','merge'); b.add_edge('merge',END)
    return b.compile()

class ServiceState(TypedDict):
    approved: bool
    user_input: str
    intent: str
    response: str
    attempts: int
    assessment: str
    status: str
    ticket_id: str
    complaint_log: Annotated[list[str],operator.add]
    path: Annotated[list[str],operator.add]

def build_service(llm=None, human_review=False):
    llm = llm if llm is not None else create_model()
    def classify(s):
        label=choice(llm,'电商意图：退货退款return、询问信息consult、投诉complaint。',
                     s['user_input'],['return','consult','complaint'])
        print('[classify] 意图：'+label)
        return {'intent':label,'path':['classify']}
    def handle(label):
        def run(s):
            n=s.get('attempts',0)+1
            print(f'[handle_{label}] 第 {n} 次处理')
            response=ask(llm,
                '你是教学电商客服。80字以内。未知商家政策应提示核实；不编造商品参数、物流、退款成功。'
                '退货询问原因并说明申请步骤；投诉应致歉并提供解决步骤。根据上次评估改进回复。',
                s['user_input']+'\n上次评估：'+s.get('assessment','首次处理'))
            return {'response':response,'attempts':n,'path':['handle_'+label]}
        return run
    def notify(s):
        text=ask(llm,'生成40字以内主管通知草稿，标明待人工发送。',s['user_input'])
        return {'complaint_log':['[待发送通知草稿] '+text], 'path':['notify_draft']}
    def ticket(s):
        # 本地记录随最终结果写入文件；一个流程固定一个ID，重试不新增工单。
        return {'complaint_log':['[本地工单] '+s['ticket_id']+'：'+s['user_input']], 'path':['local_ticket']}
    def assess(s):
        label=choice(llm,'评估客服回复是否回应问题、清晰且没有虚构完成的操作。这是模型自检，不代表用户真实满意度。',
                     s['user_input']+'\n回复：'+s['response'],['合格','不合格'])
        print('[assess] 模型自检：'+label)
        return {'assessment':label,'status':'完成' if label=='合格' else '待改进','path':['assess']}
    def route(s):
        if s['assessment']=='合格': return 'end'
        return 'handoff' if s['attempts']>=3 else s['intent']
    def handoff(s):
        return {'status':'待人工处理（本地记录）','path':['handoff']}
    def review(s):
        decision=interrupt({'工单号':s['ticket_id'],'回复草稿':s['response'],'提示':'输入yes批准，no拒绝并转人工'})
        if decision not in ('yes','no'): raise ValueError('请输入yes或no')
        return {'approved':decision=='yes','path':['review']}
    b=StateGraph(ServiceState)
    b.add_node('classify',classify); b.add_edge(START,'classify')
    mapping={label:'handle_'+label for label in ['return','consult','complaint']}
    for label,name in mapping.items(): b.add_node(name,handle(label))
    b.add_node('notify_draft',notify); b.add_node('local_ticket',ticket)
    b.add_node('assess',assess); b.add_node('handoff',handoff)
    b.add_conditional_edges('classify',lambda s:s['intent'],mapping)
    b.add_edge('handle_return','assess'); b.add_edge('handle_consult','assess')
    # 仅首次投诉处理并行准备通知和工单，重试只改进回复。
    complaint_source='handle_complaint'
    if human_review:
        b.add_node('review',review)
        b.add_node('approved_reply',lambda s:{})
        b.add_edge('handle_complaint','review')
        b.add_conditional_edges('review',lambda s:'approved_reply' if s['approved'] else 'handoff',
                                ['approved_reply','handoff'])
        complaint_source='approved_reply'
    b.add_conditional_edges(complaint_source,lambda s:['notify_draft','local_ticket'] if s['attempts']==1 else 'assess',
                            ['notify_draft','local_ticket','assess'])
    b.add_edge(['notify_draft','local_ticket'],'assess')
    b.add_conditional_edges('assess',route,dict(mapping,end=END,handoff='handoff'))
    b.add_edge('handoff',END)
    return b.compile(checkpointer=InMemorySaver() if human_review else None)
