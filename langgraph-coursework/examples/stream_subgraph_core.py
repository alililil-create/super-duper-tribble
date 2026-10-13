"""流式输出与嵌套子图，使用真实LangGraph API。"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer
from advanced_graphs import ask, choice
from qwen_config import create_model

class StoryState(TypedDict):
    topic: str
    outline: str
    story: str
    comment: str

def build_story(llm=None):
    llm=llm if llm is not None else create_model()
    def outline(s):
        print('[大纲节点] 正在生成大纲……')
        return {'outline':ask(llm,'写80字以内故事大纲。',s['topic'])}
    def write(s):
        print('[写作节点] 正在写故事……')
        return {'story':ask(llm,'依据大纲写200字以内完整故事。',s['outline'])}
    def comment(s):
        print('[点评节点] 正在点评……')
        return {'comment':ask(llm,'用50字以内点评故事。',s['story'])}
    b=StateGraph(StoryState)
    for name,fn in [('outline',outline),('write',write),('comment',comment)]: b.add_node(name,fn)
    b.add_edge(START,'outline'); b.add_edge('outline','write'); b.add_edge('write','comment'); b.add_edge('comment',END)
    return b.compile()

def show_story(mode):
    print('流式输出演示：stream_mode='+mode)
    print('主题：一只会飞的小猪')
    initial={'topic':'一只会飞的小猪','outline':'','story':'','comment':''}
    for chunk in build_story().stream(initial,stream_mode=mode):
        if mode=='values': print('\n--- 完整状态 ---\n',chunk,flush=True)
        else:
            for node,update in chunk.items():
                print('\n--- 节点 ['+node+'] 执行完毕 ---',flush=True)
                for key,value in update.items(): print(key+': '+value,flush=True)
    print('\n所有节点执行完毕！')

class ChatState(TypedDict):
    question: str
    reply: str

def build_custom(llm=None):
    llm=llm if llm is not None else create_model()
    def reply(s):
        writer=get_stream_writer()
        writer({'type':'status','text':'AI正在思考……'})
        parts=[]
        for chunk in llm.stream('请用150字以内中文回答：'+s['question']):
            if isinstance(chunk.content,str) and chunk.content:
                parts.append(chunk.content)
                writer({'type':'token','text':chunk.content})
        if not parts: raise ValueError('模型流没有返回文本')
        text=''.join(parts)
        writer({'type':'done','text':text})
        return {'reply':text}
    b=StateGraph(ChatState); b.add_node('reply',reply)
    b.add_edge(START,'reply'); b.add_edge('reply',END)
    return b.compile()

class ArticleState(TypedDict):
    topic: str
    title: str
    article: str

def build_article(llm=None):
    llm=llm if llm is not None else create_model()
    def title(s):
        print('[子图-节点1] 根据主题生成标题……')
        value=ask(llm,'只输出一个文章标题。',s['topic'])
        print('[子图-节点1] 标题：'+value)
        return {'title':value}
    def article(s):
        print('[子图-节点2] 根据标题生成内容……')
        return {'article':ask(llm,'按主题和标题写200字以内文章。',s['topic']+'\n'+s['title'])}
    sub=StateGraph(ArticleState)
    sub.add_node('title',title); sub.add_node('article',article)
    sub.add_edge(START,'title'); sub.add_edge('title','article'); sub.add_edge('article',END)
    parent=StateGraph(ArticleState)
    parent.add_node('subgraph',sub.compile())
    parent.add_edge(START,'subgraph'); parent.add_edge('subgraph',END)
    return parent.compile()

class CustomerState(TypedDict):
    user_message: str
    intent: str
    complaint_type: str
    reply: str

def build_customer_subgraph(llm=None):
    llm=llm if llm is not None else create_model()
    def intent(s):
        label=choice(llm,'判断用户意图。',s['user_message'],['投诉','咨询','其他'])
        print('[主图] 意图识别：'+label)
        return {'intent':label}
    def classify(s):
        print('[子图] 投诉分类中……')
        label=choice(llm,'判断投诉类别。',s['user_message'],['质量','物流','服务','其他'])
        print('[子图] 投诉分类结果：'+label)
        return {'complaint_type':label}
    def response(s):
        text=ask(llm,'你是教学客服。100字内礼貌回应投诉，询问核实所需信息。不要虚构已核实、已退款、处理时限或商家政策。',s['user_message'])
        print('[子图] 回复已生成')
        return {'reply':text}
    sub=StateGraph(CustomerState)
    sub.add_node('classify_complaint',classify); sub.add_node('generate_reply',response)
    sub.add_edge(START,'classify_complaint'); sub.add_edge('classify_complaint','generate_reply'); sub.add_edge('generate_reply',END)
    def other(s):
        print('[主图] 处理'+s['intent'])
        return {'reply':ask(llm,'客服简洁回答；未知商家政策请建议核实，不编造。',s['user_message'])}
    b=StateGraph(CustomerState)
    b.add_node('classify',intent); b.add_node('complaint_subgraph',sub.compile())
    b.add_node('consult',other); b.add_node('other',other)
    b.add_edge(START,'classify')
    b.add_conditional_edges('classify',lambda s:s['intent'],{'投诉':'complaint_subgraph','咨询':'consult','其他':'other'})
    for name in ['complaint_subgraph','consult','other']: b.add_edge(name,END)
    return b.compile()
