"""图片 3：计算器工具。"""
from common import banner
from toolkit import calculator, run_agent

def main():
    banner()
    for title, expression in [('测试1：简单加法', '125 + 378'), ('测试2：复杂运算', '(15 + 27) * 3 - 18 / 2')]:
        print('=' * 50 + '\n' + title + '\n' + '=' * 50)
        run_agent('请帮我计算 ' + expression, [calculator], ('calculator', {'expression': expression}))
        print()

if __name__ == '__main__':
    main()

