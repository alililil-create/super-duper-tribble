from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator

class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("密码 UTF-8 编码不能超过 72 字节")
        return value

class UserCreate(LoginRequest):
    email: EmailStr = Field(max_length=100)

class UserOut(Schema):
    id: int
    username: str
    email: str
    created_at: datetime

class ArticleCreate(Schema):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=20, max_length=15000)
    level: str = Field(default="B1", min_length=1, max_length=20)
    source: str = Field(default="user_upload", max_length=200)

class ArticleBrief(Schema):
    id: int
    title: str
    level: str
    source: str
    created_at: datetime

class ArticleOut(ArticleBrief):
    content: str

class AIRole(Schema):
    name: str = Field(min_length=1, max_length=100)
    stance: str = Field(min_length=1, max_length=2000)
    example: str = Field(min_length=1, max_length=2000)

class TaskStep(Schema):
    stage: str = Field(min_length=1, max_length=100)
    task: str = Field(min_length=1, max_length=2000)
    user_action: str = Field(min_length=1, max_length=2000)

Difficulty = Literal["simple", "standard", "challenge"]

class SceneCard(Schema):
    title: str = Field(min_length=1, max_length=200)
    user_role: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=4000)
    ai_roles: list[AIRole] = Field(min_length=1, max_length=5)
    conflict: str = Field(min_length=1, max_length=4000)
    task_chain: list[TaskStep] = Field(min_length=1, max_length=8)
    language_goals: str = Field(min_length=1, max_length=4000)
    final_output: str = Field(min_length=1, max_length=4000)
    difficulty: Difficulty = "standard"

class SceneGenerateRequest(Schema):
    article_id: int = Field(gt=0)
    difficulty: Difficulty = "standard"

class SceneOut(SceneCard):
    id: int
    article_id: int
    created_at: datetime

class SessionCreate(Schema):
    article_id: int = Field(gt=0)
    scene_id: int = Field(gt=0)

class SessionOut(SessionCreate):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

class SessionDetail(SessionOut):
    scene: SceneOut

class MessageCreate(Schema):
    content: str = Field(min_length=1, max_length=2000)

class MessageOut(MessageCreate):
    id: int
    session_id: int
    role: str
    created_at: datetime

class SendMessageResponse(Schema):
    user_message: MessageOut
    ai_message: MessageOut
