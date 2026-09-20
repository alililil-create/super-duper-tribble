"""图片 6：同一提示词，比较三种温度。单次结果不能证明随机性趋势。"""
from langchain_core.messages import HumanMessage
from common import banner, model

def main():
    banner()
    prompt = '为一款可以提醒喝水、调节水温的智能水杯写一句广告语，只输出广告语。'
    for temperature, label in [(0.0, '最保守'), (0.7, '中等创意'), (1.5, '高创意（放飞自我）')]:
        print(f'【Temperature = {temperature}】{label}')
        print('=' * 50)
        print(model(temperature).invoke([HumanMessage(content=prompt)]).content)
        print('=' * 50 + '\n')

if __name__ == '__main__':
    main()

