"""真实批量运行新增八项；审批以明确标注的测试输入验证，不冒充人工审批。"""
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parent

def main():
    logs=ROOT/'runs'; logs.mkdir(exist_ok=True)
    thread='verify-'+uuid4().hex[:12]
    commands=[
        ('10_human_interaction',['--decision','yes']),
        ('11_customer_service_review',['--decision','no']),
        ('12_checkpoints',[]),
        ('13_persistence',['start','--thread',thread]),
        ('13_persistence',['resume','--thread',thread,'--decision','yes']),
        ('13_persistence',['show','--thread',thread]),
        ('14_conditional_edges',[]),('15_cycle',[]),('16_parallel',[]),
        ('17_routed_customer_service',[]),('18_compile_validation',[]),('19_question_workflow',[]),
        ('20_sqlite_saved_answer',['--thread',thread]),('20_sqlite_saved_answer',['--thread',thread])]
    outputs={}
    for name,args in commands:
        command=[sys.executable,'-u',str(ROOT/'examples'/(name+'.py')),*args]
        print('\n> '+name+' '+' '.join(args),flush=True)
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',
                              env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1'),timeout=300)
        text=result.stdout+result.stderr+f'\n退出码：{result.returncode}\n'
        print(text,flush=True)
        outputs[name]=outputs.get(name,'')+'\n命令参数：'+' '.join(args)+'\n'+text
        (logs/(name+'.txt')).write_text(outputs[name],encoding='utf-8')
        if result.returncode: raise SystemExit('运行失败：'+name)
    print('10至20项全部运行成功；持久化与答案读档由独立子进程验证。')

if __name__=='__main__': main()
