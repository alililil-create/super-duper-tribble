"""读取项目根目录配置；不打印密钥，不提供假回复。"""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def create_model():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    key = os.getenv('LLM_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
    if not key:
        raise RuntimeError('请在项目 .env 中配置 LLM_API_KEY。')
    return ChatOpenAI(model=os.getenv('LLM_MODEL_ID', 'qwen-plus'), api_key=key,
                      base_url=os.getenv('LLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
                      temperature=0, timeout=45, max_retries=1)
