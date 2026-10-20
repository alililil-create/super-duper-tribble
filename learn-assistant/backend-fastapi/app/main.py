from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from app.db import Base, engine, get_db
from app.models import User, Article, Scene, LearningSession, Message, utcnow
from app.schemas import *
from app.auth import current_user, hash_password, verify_password, token_for
from app import llm

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="文章驱动英语学习助手", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
DB = Depends(get_db)
AUTH = Depends(current_user)
# Single-process coursework server: reject overlapping turns in the same session.
# Multi-worker deployment requires a distributed lock or database task queue.
busy_sessions: set[int] = set()

@app.get("/api/health", tags=["环境"])
async def health(db: AsyncSession = DB):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": engine.dialect.name}

@app.post("/api/auth/register", response_model=UserOut, status_code=201, tags=["登录注册"])
async def register(payload: UserCreate, db: AsyncSession = DB):
    user = User(username=payload.username, email=str(payload.email), hashed_password=await run_in_threadpool(hash_password, payload.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "用户名或邮箱已注册")
    await db.refresh(user)
    return user

@app.post("/api/auth/login", tags=["登录注册"])
async def login(payload: LoginRequest, db: AsyncSession = DB):
    user = await db.scalar(select(User).where(User.username == payload.username))
    if not user or not await run_in_threadpool(verify_password, payload.password, user.hashed_password):
        raise HTTPException(401, "用户名或密码错误")
    return {"access_token": token_for(user.id), "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserOut, tags=["登录注册"])
async def me(user: User = AUTH):
    return user

@app.post("/api/articles", response_model=ArticleOut, status_code=201, tags=["文章"])
async def create_article(payload: ArticleCreate, db: AsyncSession = DB, user: User = AUTH):
    article = Article(**payload.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article

@app.get("/api/articles", response_model=list[ArticleBrief], tags=["文章"])
async def articles(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), db: AsyncSession = DB, user: User = AUTH):
    return (await db.scalars(select(Article).order_by(Article.created_at.desc(), Article.id.desc()).offset((page-1)*page_size).limit(page_size))).all()

@app.get("/api/articles/{article_id}", response_model=ArticleOut, tags=["文章"])
async def article_detail(article_id: int, db: AsyncSession = DB, user: User = AUTH):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    return article

@app.post("/api/scenes/generate", response_model=SceneOut, status_code=201, tags=["场景"])
async def generate(payload: SceneGenerateRequest, db: AsyncSession = DB, user: User = AUTH):
    article = await db.get(Article, payload.article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    # Release read transaction while awaiting the remote model.
    await db.commit()
    card = await llm.generate_scene(article, payload.difficulty)
    scene = Scene(article_id=article.id, **card.model_dump())
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene

@app.get("/api/scenes", response_model=list[SceneOut], tags=["场景"])
async def scenes(article_id: int | None = Query(None, gt=0), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), db: AsyncSession = DB, user: User = AUTH):
    stmt = select(Scene).order_by(Scene.id.desc())
    if article_id is not None:
        stmt = stmt.where(Scene.article_id == article_id)
    return (await db.scalars(stmt.offset((page-1)*page_size).limit(page_size))).all()

@app.get("/api/scenes/{scene_id}", response_model=SceneOut, tags=["场景"])
async def scene_detail(scene_id: int, db: AsyncSession = DB, user: User = AUTH):
    scene = await db.get(Scene, scene_id)
    if not scene:
        raise HTTPException(404, "场景不存在")
    return scene

async def owned_session(db, session_id, user_id):
    session = await db.scalar(select(LearningSession).where(LearningSession.id == session_id, LearningSession.user_id == user_id))
    if not session:
        raise HTTPException(404, "学习会话不存在")
    return session

@app.get("/api/sessions", response_model=list[SessionOut], tags=["学习会话"])
async def list_sessions(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), db: AsyncSession = DB, user: User = AUTH):
    return (await db.scalars(select(LearningSession).where(LearningSession.user_id == user.id).order_by(LearningSession.updated_at.desc(), LearningSession.id.desc()).offset((page-1)*page_size).limit(page_size))).all()

@app.get("/api/sessions/{session_id}/report", tags=["学习报告"])
async def learning_report(session_id: int, db: AsyncSession = DB, user: User = AUTH):
    from app.report import build_report
    session = await owned_session(db, session_id, user.id)
    scene = await db.get(Scene, session.scene_id)
    history = (await db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.id))).all()
    return build_report(session, scene, history)

@app.post("/api/sessions", response_model=SessionOut, status_code=201, tags=["学习会话"])
async def create_session(payload: SessionCreate, db: AsyncSession = DB, user: User = AUTH):
    scene = await db.get(Scene, payload.scene_id)
    if not scene or scene.article_id != payload.article_id:
        raise HTTPException(404, "该文章下不存在此场景")
    stmt = select(LearningSession).where(LearningSession.user_id == user.id, LearningSession.scene_id == scene.id)
    existing = await db.scalar(stmt)
    if existing:
        return existing
    session = LearningSession(user_id=user.id, **payload.model_dump())
    db.add(session)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(stmt)
        if existing:
            return existing
        raise HTTPException(409, "会话创建冲突，请重试")
    await db.refresh(session)
    return session

@app.get("/api/sessions/{session_id}", response_model=SessionDetail, tags=["学习会话"])
async def session_detail(session_id: int, db: AsyncSession = DB, user: User = AUTH):
    session = await owned_session(db, session_id, user.id)
    scene = await db.get(Scene, session.scene_id)
    return {**SessionOut.model_validate(session).model_dump(), "scene": scene}

@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut], tags=["学习会话"])
async def messages(session_id: int, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), db: AsyncSession = DB, user: User = AUTH):
    await owned_session(db, session_id, user.id)
    return (await db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.id).offset(offset).limit(limit))).all()

@app.post("/api/sessions/{session_id}/messages", response_model=SendMessageResponse, tags=["学习会话"])
async def send_message(session_id: int, payload: MessageCreate, db: AsyncSession = DB, user: User = AUTH):
    session = await owned_session(db, session_id, user.id)
    if session_id in busy_sessions:
        raise HTTPException(409, "上一条消息仍在回复中")
    busy_sessions.add(session_id)
    try:
        scene = await db.get(Scene, session.scene_id)
        human = Message(session_id=session_id, role="user", content=payload.content)
        db.add(human)
        session.updated_at = utcnow()
        await db.commit()
        await db.refresh(human)
        history = list(reversed((await db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.id.desc()).limit(10))).all()))
        await db.commit()
        reply = await llm.generate_reply(scene, history)
        ai = Message(session_id=session_id, role="assistant", content=reply)
        db.add(ai)
        session.updated_at = utcnow()
        await db.commit()
        await db.refresh(ai)
        return {"user_message": human, "ai_message": ai}
    finally:
        busy_sessions.discard(session_id)
