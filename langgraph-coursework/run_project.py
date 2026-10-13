"""逐项真实运行本次六个模块，并保存原始输出。"""
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    for script in sorted((ROOT/'examples').glob('class[23][0-9]_*.py')):
        print('\n> '+script.name,flush=True)
        output=[]
        with subprocess.Popen([sys.executable,'-u',str(script)],cwd=ROOT,
             env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1'),
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8') as process:
            for line in process.stdout:
                print(line,end='',flush=True); output.append(line)
            code=process.wait()
        (ROOT/'runs'/(script.stem+'.txt')).write_text(''.join(output)+f'\n退出码：{code}\n',encoding='utf-8')
        if code: raise SystemExit(code)
    print('本次6项全部真实运行完成。')
if __name__=='__main__': main()
