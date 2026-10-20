"""Run against the real API/MySQL/Qwen server. No simulated replies."""
import json
import secrets
import httpx
from pathlib import Path
from datetime import datetime

def main():
    lines=[]
    def out(message):
        print(message,flush=True);lines.append(str(message))
    with httpx.Client(base_url="http://127.0.0.1:8000/api",timeout=150,trust_env=False) as c:
        def request(method,path,body=None,headers=None):
            r=c.request(method,path,json=body,headers=headers)
            if r.is_error:
                raise RuntimeError(f'{method} {path}: {r.status_code} {r.text}')
            return r.json()
        out('=== 阶段 0–3：真实 MySQL + 千问接口验收 ===')
        out('运行时间：'+datetime.now().isoformat(timespec='seconds'))
        out('健康检查：'+json.dumps(request('GET','/health'),ensure_ascii=False))
        suffix=secrets.token_hex(3)
        passwords=secrets.token_urlsafe(12)
        users={}
        for name in ['alice','bob']:
            payload={'username':name+'_'+suffix,'email':name+'_'+suffix+'@example.com','password':passwords}
            user=request('POST','/auth/register',payload)
            login=request('POST','/auth/login',payload)
            users[name]={'Authorization':'Bearer '+login['access_token']}
            out(f"注册与登录成功：{user['username']}，用户 ID={user['id']}（不输出密码或令牌）")
        a=users['alice'];b=users['bob']
        article=request('POST','/articles',{'title':'Urban Gardens and Our Community','content':'A neighborhood plans to turn an empty rooftop into a community garden. Volunteers want to grow vegetables and flowers. Some residents worry about the cost, noise, and safety. The community must agree on a budget and a weekly schedule before starting the project.','level':'B1','source':'课程原创练习素材'},a)
        out(f"\n[文章上传] ID={article['id']} 标题={article['title']}")
        out('[文章查询] '+request('GET',f"/articles/{article['id']}",headers=a)['content'])
        out('\n[场景生成] 正在真实调用千问，请等待……')
        scene=request('POST','/scenes/generate',{'article_id':article['id'],'difficulty':'standard'},a)
        saved=request('GET',f"/scenes/{scene['id']}",headers=a)
        out('[场景查询] 已从 MySQL 读取生成结果：\n'+json.dumps(saved,ensure_ascii=False,indent=2))
        session=request('POST','/sessions',{'article_id':article['id'],'scene_id':scene['id']},a)
        out(f"\n[学习会话] ID={session['id']}")
        for path in [f"/sessions/{session['id']}",f"/sessions/{session['id']}/messages"]:
            response=c.get(path,headers=b)
            assert response.status_code==404
            out(f'[多用户隔离] Bob 访问 Alice {path} → 404，通过')
        out('\n[发送消息] I suggest starting with a small garden to keep costs low.')
        reply=request('POST',f"/sessions/{session['id']}/messages",{'content':'I suggest starting with a small garden to keep costs low.'},a)
        out('[千问角色回复] '+reply['ai_message']['content'])
        history=request('GET',f"/sessions/{session['id']}/messages",headers=a)
        assert len(history)==2
        out('[消息持久化] 查询到用户消息与 AI 回复，共 2 条')
        out('\n全部在线验收通过。')
    dest=Path(__file__).resolve().parents[2]/'evidence'
    dest.mkdir(exist_ok=True)
    (dest/'online-run.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
