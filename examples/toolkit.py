"""真实本地工具与有界工具调用循环。"""
import ast
import operator
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from common import OFFLINE, model

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

def safe_calculate(expression):
    if len(expression) > 200:
        raise ValueError('表达式过长')
    tree = ast.parse(expression, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise ValueError('表达式过于复杂')
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1e12:
                raise ValueError('数字超出范围')
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            result = OPS[type(node.op)](visit(node.left), visit(node.right))
            if abs(result) > 1e100:
                raise ValueError('结果超出范围')
            return result
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        raise ValueError('仅支持数字、括号及加减乘除')
    return visit(tree.body)

@tool
def calculator(expression: str) -> str:
    """计算只含数字、括号和加减乘除的数学表达式，例如 (15+27)*3-18/2。"""
    try:
        return f'计算结果：{expression} = {safe_calculate(expression)}'
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as error:
        return f'计算失败：{error}'

def beijing_now():
    return datetime.now(timezone(timedelta(hours=8)))

@tool
def get_current_time() -> str:
    """获取当前北京时间（UTC+08:00）的日期和时分秒。"""
    return '当前时间：' + beijing_now().strftime('%Y年%m月%d日 %H:%M:%S') + '（北京时间）'

@tool
def get_weekday() -> str:
    """获取北京时间今天是星期几。"""
    return '今天是：星期' + '一二三四五六日'[beijing_now().weekday()]

def run_agent(question, tools, offline_call=None):
    print('问题：' + question)
    lookup = {item.name: item for item in tools}
    if OFFLINE:
        if offline_call is None:
            print('离线模式：此问题未预设工具路由。')
            return
        name, args = offline_call
        print('调用工具：' + name + '（离线预设路由）')
        print('工具返回：' + lookup[name].invoke(args))
        return
    llm = model(0).bind_tools(tools)
    messages = [SystemMessage(content='你是简洁的助手。计算和查询当前时间必须调用对应工具，收到结果后用中文回答。'), HumanMessage(content=question)]
    for _ in range(6):
        response = llm.invoke(messages)
        messages.append(response)
        if not response.tool_calls:
            print('最终回答：' + response.content)
            return
        for call in response.tool_calls:
            print('调用工具：' + call['name'])
            print('工具参数：' + str(call['args']))
            if call['name'] not in lookup:
                result = '未知工具'
            else:
                result = lookup[call['name']].invoke(call['args'])
            print('工具返回：' + str(result))
            messages.append(ToolMessage(content=str(result), tool_call_id=call['id']))
    raise RuntimeError('工具调用超过6轮，已停止')

