"""图片 1：五轮点餐对话，逐轮传入完整消息历史。仅教学模拟订单。"""
from langchain_core.messages import HumanMessage, SystemMessage
from common import banner, model

def main():
    banner()
    llm = model()
    messages = [SystemMessage(content='你是餐厅服务员，礼貌简洁，记住用户点的菜。此为教学模拟点餐，不连接真实餐厅。')]
    print(f'[SystemMessage] {messages[0].content}')
    for question in ['你好，我想点餐', '来一份宫保鸡丁', '再来一碗米饭', '帮我看看我都点了什么', '就这些了，帮我下单']:
        messages.append(HumanMessage(content=question))
        print(f'[HumanMessage] {question}')
        response = llm.invoke(messages)
        messages.append(response)
        print(f'[AIMessage] {response.content}')
    print(f'\n历史消息数：{len(messages)}（1 条系统消息 + 5 轮问答）')
    return messages

if __name__ == '__main__':
    main()

