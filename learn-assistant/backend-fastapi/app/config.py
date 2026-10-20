from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = Field(min_length=32)
    DASHSCOPE_API_KEY: SecretStr = SecretStr("")
    LLM_MODEL_ID: str = "qwen-plus"
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")

settings = Settings()
