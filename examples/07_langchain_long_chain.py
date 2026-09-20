"""图片 2：增加分隔线和字符统计（中文不能用空格准确统计词数）。"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from common import banner, model

def add_separator(text):
    return '=' * 50 + '\n' + text + '\n' + '=' * 50

def count_words(text):
    body = text.split('\n', 1)[1].rsplit('\n', 1)[0]
    count = sum(not char.isspace() for char in body)
    return text + f'\n正文字符数：{count}（含标点，不含空白与分隔线）'

def main():
    banner()
    prompt = ChatPromptTemplate.from_template('请用{style}的风格，100字以内介绍{topic}。')
    llm, parser = model(), StrOutputParser()
    chain = prompt | llm | parser | add_separator | count_words
    print('chain = prompt | llm | parser | add_separator | count_words')
    print('扩展链的输出（5 个组件）：')
    print(chain.invoke({'topic': 'Python 编程', 'style': '幽默'}))

if __name__ == '__main__':
    main()

