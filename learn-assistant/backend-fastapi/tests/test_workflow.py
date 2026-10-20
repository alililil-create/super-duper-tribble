"""Isolated API tests use SQLite and explicit model stubs, never as demo output."""
import os
import asyncio
import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-0123456789-abcdef-0123456789"
from app.main import app
from app import llm
from app.schemas import SceneCard

CARD = dict(title="社区花园会议", user_role="志愿者", goal="提出绿色方案", ai_roles=[dict(name="Alex", stance="支持", example="What is your plan?")], conflict="预算有限", task_chain=[dict(stage="讨论", task="介绍方案", user_action="用英语提出建议")], language_goals="建议句型", final_output="英文提案", difficulty="standard")

@pytest.fixture
def client(monkeypatch):
    async def scene(*args): return SceneCard(**CARD)
    async def reply(scene, history):
        assert history[-1].role == "user"
        assert sum(m.content == history[-1].content for m in history) == 1
        return "How can we make your plan work?"
    monkeypatch.setattr(llm, "generate_scene", scene)
    monkeypatch.setattr(llm, "generate_reply", reply)
    with TestClient(app) as c:
        yield c

def account(c, name):
    payload = dict(username=name, email=name+"@example.com", password="Strong123!")
    result = c.post("/api/auth/register", json=payload)
    assert result.status_code == 201
    assert "hashed_password" not in result.json()
    token = c.post("/api/auth/login", json=payload).json()["access_token"]
    return {"Authorization": "Bearer "+token}

def setup_scene(c, headers):
    article = c.post("/api/articles", headers=headers, json=dict(title="Urban gardens", content="Our community wants to build a green garden together.")).json()
    result = c.post("/api/scenes/generate", headers=headers, json=dict(article_id=article["id"]))
    assert result.status_code == 201
    return article, result.json()

def test_auth_and_validation(client):
    c=client
    assert c.get("/api/articles").status_code == 401
    h=account(c,"alice")
    assert c.get("/api/users/me",headers=h).json()["username"] == "alice"
    assert c.post("/api/auth/register",json=dict(username="alice",email="new@example.com",password="abcdef")).status_code == 409
    assert c.post("/api/auth/login",json=dict(username="alice",password="wrong123")).status_code == 401
    assert c.get("/api/users/me",headers={"Authorization":"Bearer bad"}).status_code == 401
    assert c.get("/api/articles?page_size=100",headers=h).status_code == 422
    assert c.post("/api/auth/register",json=dict(username="longpassword",email="long@example.com",password="密"*30)).status_code == 422
    assert c.post("/api/articles",headers=h,json=dict(title="   ",content="x"*25)).status_code == 422

def test_shared_material_private_sessions(client):
    c=client; a=account(c,"alice"); b=account(c,"bob")
    article,scene=setup_scene(c,a)
    assert c.get(f'/api/articles/{article["id"]}',headers=b).status_code == 200
    assert "content" not in c.get('/api/articles',headers=a).json()[0]
    assert c.get('/api/scenes?article_id='+str(article['id']),headers=b).json()[0]['id']==scene['id']
    body=dict(article_id=article['id'],scene_id=scene['id'])
    sid=c.post('/api/sessions',headers=a,json=body).json()['id']
    assert c.post('/api/sessions',headers=a,json=body).json()['id']==sid
    assert c.post('/api/sessions',headers=b,json=body).json()['id']!=sid
    assert c.get(f'/api/sessions/{sid}',headers=b).status_code==404
    assert c.get(f'/api/sessions/{sid}/messages',headers=b).status_code==404
    assert c.post(f'/api/sessions/{sid}/messages',headers=b,json={'content':'Hi'}).status_code==404
    result=c.post(f'/api/sessions/{sid}/messages',headers=a,json={'content':'I suggest planting flowers.'})
    assert result.status_code==200,result.text
    msgs=c.get(f'/api/sessions/{sid}/messages',headers=a).json()
    assert [m['role'] for m in msgs]==['user','assistant']
    report=c.get(f'/api/sessions/{sid}/report',headers=a).json()
    assert report['user_messages']==1 and report['ai_messages']==1
    assert report['english_words']==4 and report['unique_english_words']==4
    assert report['expressions'][0]['content']=='I suggest planting flowers.'
    assert c.get(f'/api/sessions/{sid}/report',headers=b).status_code==404
    assert all(s['id']!=sid for s in c.get('/api/sessions',headers=b).json())
    assert len(c.get(f'/api/sessions/{sid}/messages?limit=1&offset=1',headers=a).json())==1
    assert c.post('/api/sessions',headers=a,json=dict(article_id=999,scene_id=scene['id'])).status_code==404

def test_failed_llm_preserves_user_message(client,monkeypatch):
    c=client;h=account(c,'alice');a,s=setup_scene(c,h)
    sid=c.post('/api/sessions',headers=h,json=dict(article_id=a['id'],scene_id=s['id'])).json()['id']
    async def broken(*args): raise HTTPException(502,'upstream unavailable')
    monkeypatch.setattr(llm,'generate_reply',broken)
    assert c.post(f'/api/sessions/{sid}/messages',headers=h,json={'content':'Keep this message.'}).status_code==502
    saved=c.get(f'/api/sessions/{sid}/messages',headers=h).json()
    assert len(saved)==1 and saved[0]['content']=='Keep this message.'

def test_scene_validation_retry(monkeypatch):
    from types import SimpleNamespace
    calls=[]
    async def response(*args,**kwargs):
        calls.append(1)
        return 'invalid json' if len(calls)==1 else json.dumps(CARD)
    monkeypatch.setattr(llm,'completion',response)
    card=asyncio.run(llm.generate_scene(SimpleNamespace(title='Test',content='Article'),'standard'))
    assert card.title==CARD['title'] and len(calls)==2
    async def invalid(*args,**kwargs): return '{}'
    monkeypatch.setattr(llm,'completion',invalid)
    with pytest.raises(HTTPException) as error:
        asyncio.run(llm.generate_scene(SimpleNamespace(title='Test',content='Article'),'standard'))
    assert error.value.status_code==502

def test_report_empty_and_repeated_words():
    from types import SimpleNamespace as Obj
    from app.report import build_report
    session=Obj(id=1,created_at='now',updated_at='now')
    scene=Obj(title='练习',difficulty='standard',goal='交流',language_goals='建议')
    empty=build_report(session,scene,[])
    assert empty['english_words']==0 and empty['expressions']==[]
    result=build_report(session,scene,[Obj(id=1,role='user',content='Hello hello garden.'),Obj(id=2,role='assistant',content='Good. [Hint] Try a longer sentence.')])
    assert result['english_words']==3 and result['unique_english_words']==2
    assert result['hints'][0]['message_id']==2
