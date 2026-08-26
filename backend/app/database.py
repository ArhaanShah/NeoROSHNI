from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    pass


if settings.database_url.startswith("sqlite"):
    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        future=True,
    )
else:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True, poolclass=NullPool)

db_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_session_factory() as session:
        yield session
