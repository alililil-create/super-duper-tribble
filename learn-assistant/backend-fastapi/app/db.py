from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

class Base(DeclarativeBase):
    pass

# SQLite is used only by isolated automated tests. Local coursework uses MySQL.
options = {} if settings.DATABASE_URL.startswith("sqlite") else {"pool_size": 10, "max_overflow": 20}
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False, **options)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_db():
    async with SessionLocal() as db:
        yield db
