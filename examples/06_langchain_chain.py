"""图片 2：提示词模板 | 模型 | 输出解析器。"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from common import banner, model

def main():
    banner()
    prompt = ChatPromptTemplate.from_template('请用100字以内介绍{topic}。')
    chain = prompt | model() | StrOutputParser()
    print('chain = prompt | llm | parser')
    print('链的输出结果：')
    print(chain.invoke({'topic': '机器学习'}))

if __name__ == '__main__':
    main()

