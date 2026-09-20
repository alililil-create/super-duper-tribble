"""图片 4：当前时间与星期查询。"""
from common import banner
from toolkit import get_current_time, get_weekday, run_agent

def main():
    banner()
    for title, question, tool_name in [('测试1：获取当前时间', '现在几点了？', 'get_current_time'), ('测试2：获取星期几', '今天是星期几？', 'get_weekday')]:
        print('=' * 50 + '\n' + title + '\n' + '=' * 50)
        run_agent(question, [get_current_time, get_weekday], (tool_name, {}))
        print()

if __name__ == '__main__':
    main()
