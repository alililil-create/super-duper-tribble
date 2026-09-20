"""图片 5：千问基础调用。"""
from langchain_core.messages import HumanMessage, SystemMessage
from common import banner, model

def main():
    banner()
    response = model().invoke([SystemMessage(content='你是一个友善的助手，回答简洁。'),
                               HumanMessage(content='你好，请用一句话介绍你自己。')])
    print(response.content)

if __name__ == '__main__':
    main()

