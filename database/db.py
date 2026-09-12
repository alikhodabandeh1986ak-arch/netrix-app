"""
اتصال به دیتابیس (async). با Supabase/Neon/هر Postgres دیگه کار می‌کنه.
نکته: توی DATABASE_URL باید از درایور asyncpg استفاده بشه، یعنی مثلا:
postgresql+asyncpg://user:pass@host:5432/dbname
"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from database.models import Base

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """جداول رو در صورت نبودن می‌سازه. (برای تغییرات جدی‌تر بعدا Alembic اضافه می‌کنیم.)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
