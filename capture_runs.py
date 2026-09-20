"""执行示例，保存原始日志，再对黑底日志页面截图；不伪装原生终端截图。"""
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
GROUPS = [
    ('01_基础调用', ['class1.py']),
    ('02_温度对比', ['class2_temperature.py']),
    ('03_点餐记忆', ['class3_memory.py']),
    ('04_链式处理', ['06_langchain_chain.py', '07_langchain_long_chain.py']),
    ('05_计算器工具', ['class5_calc_tool.py']),
    ('06_时间工具', ['class6_time_tool.py']),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--browser', help='可选：Chromium / Edge 可执行文件路径')
    args = parser.parse_args()
    mode = 'offline' if args.offline else 'online'
    output = ROOT / 'runs' / mode
    output.mkdir(parents=True, exist_ok=True)
    records = []
    pages = []
    for name, scripts in GROUPS:
        chunks = []
        for script in scripts:
            command = [sys.executable, '-u', str(ROOT / 'examples' / script)]
            if args.offline:
                command.append('--offline')
            visible = 'python .\\examples\\' + script + (' --offline' if args.offline else '')
            env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
            started = datetime.now().astimezone().isoformat(timespec='seconds')
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                       encoding='utf-8', env=env, timeout=600)
            log = completed.stdout + completed.stderr
            chunks.append(f'> {visible}\n\n{log}\n[进程退出码：{completed.returncode}]\n')
            records.append(dict(script=script, command=command, started=started,
                                exit_code=completed.returncode, mode=mode))
            print(f'{script}: exit {completed.returncode}', flush=True)
        transcript = '\n'.join(chunks)
        (output / f'{name}.txt').write_text(transcript, encoding='utf-8')
        label = '离线演示 · 模型回复为教学替身' if args.offline else '千问在线运行'
        page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<style>*{box-sizing:border-box}body{margin:0;background:#101010;color:#d4d4d4;font:23px/1.65 Consolas,"Microsoft YaHei",monospace}
main{padding:26px 34px 32px;width:1600px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #383838;padding-bottom:15px;margin-bottom:20px;color:#eee}
small{font:16px/1.4 "Microsoft YaHei",sans-serif;color:#dfb66b}pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere}footer{font:15px/1.6 "Microsoft YaHei",sans-serif;color:#858585;border-top:1px solid #303030;margin-top:22px;padding-top:12px}</style>
<main><header>''' + html.escape(name.replace('_',' / ')) + '<small>' + label + '</small></header><pre>' + html.escape(transcript) + '</pre><footer>实际执行日志的终端风格页面截图 · 原始输出见同名 TXT · ' + html.escape(records[-1]['started']) + '</footer></main></html>'
        path = output / f'{name}.html'
        path.write_text(page, encoding='utf-8')
        pages.append((name, path))
    (output / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    with sync_playwright() as p:
        options = {'headless': True}
        if args.browser:
            options['executable_path'] = args.browser
        elif Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe').exists():
            options['channel'] = 'msedge'
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1600, 'height': 900}, device_scale_factor=1)
        for name, path in pages:
            page.goto(path.as_uri())
            page.evaluate('document.fonts.ready')
            page.locator('main').screenshot(path=str(output / f'{name}.png'))
        browser.close()
    index = '<!doctype html><meta charset="utf-8"><title>运行截图</title><style>body{max-width:1400px;margin:32px auto;background:#202020;color:#eee;font:18px "Microsoft YaHei"}img{width:100%;margin:12px 0 30px}a{color:#9cdcfe}</style><h1>LangChain + Qwen 运行记录</h1><p>' + label + '。图片为实际执行日志的页面截图，不是原生 PowerShell 窗口截图。</p>'
    for name, _ in pages:
        index += f'<h2>{name}</h2><a href="{name}.txt">原始日志</a> · <a href="{name}.png">PNG 图片</a><img src="{name}.png">'
    (output / 'index.html').write_text(index, encoding='utf-8')
    if any(record['exit_code'] != 0 for record in records):
        raise SystemExit('至少一个示例失败，请检查日志；失败不会被替换为演示成功。')

if __name__ == '__main__':
    main()

