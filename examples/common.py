"""公共配置。默认真实调用；只有显式 --offline 才使用教学替身。"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
OFFLINE = '--offline' in sys.argv

def banner():
    if OFFLINE:
        print('[离线演示] 模型文本由教学替身生成，未调用千问 API。')
        print('计算器、时钟、消息历史和 LCEL 管道由本机真实执行。\n')
    else:
        print(f'[在线运行] 模型：{os.getenv("LLM_MODEL_ID", "qwen-plus")}\n')

def offline_response(value, temperature=0.7):
    """只支持随附课堂用例的替身，不具备通用语言模型能力。"""
    messages = value.to_messages() if hasattr(value, 'to_messages') else value
    text = messages[-1].content
    history = '\n'.join(m.content for m in messages if isinstance(m, HumanMessage))
    if '餐厅' in messages[0].content:
        order = []
        if '宫保鸡丁' in history:
            order.append('宫保鸡丁一份')
        if '米饭' in history:
            order.append('米饭一碗')
        if '下单' in text:
            reply = '教学模拟订单已确认：' + '、'.join(order) + '。请稍等！'
        elif '点了什么' in text:
            reply = '您点了' + '、'.join(order) + '，请确认。'
        elif '宫保鸡丁' in text:
            reply = '好的，一份宫保鸡丁。请问还需要其他菜吗？'
        elif '米饭' in text:
            reply = '好的，一碗米饭。还需要加点什么吗？'
        else:
            reply = '您好！欢迎光临，请问您想点些什么？'
    elif '广告' in text:
        reply = {0.0:'智能提醒喝水，温度随心调，健康生活从一杯开始。',
                 0.7:'让每一口都温暖刚好，智能水杯陪你养成喝水好习惯。',
                 1.5:'把温暖装进口袋，让水杯当你的喝水小闹钟！'}[temperature]
    elif '机器学习' in text:
        reply = '机器学习是人工智能的重要分支，让计算机从数据中学习规律，并据此进行预测或决策，常用于图像识别、语音识别和推荐系统。'
    elif 'Python' in text:
        reply = 'Python 像编程界的万能工具箱：语法好读，工具丰富。让重复工作交给程序，把时间留给咖啡！'
    else:
        reply = '你好！这是千问基础调用示例的离线教学回复，可演示问答程序的输入输出流程。'
    return AIMessage(content=reply)

def model(temperature=0.7):
    if OFFLINE:
        return RunnableLambda(lambda value: offline_response(value, temperature))
    key = os.getenv('LLM_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
    if not key or key.startswith('sk-your'):
        raise SystemExit('缺少 API Key：请配置项目 .env；或显式添加 --offline 运行教学演示。')
    return ChatOpenAI(model=os.getenv('LLM_MODEL_ID', 'qwen-plus'), api_key=key,
                      base_url=os.getenv('LLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
                      temperature=temperature, timeout=60, max_retries=1)

