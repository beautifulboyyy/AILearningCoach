from pathlib import Path
import tempfile

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import *  # noqa: F401,F403 - 注册所有模型


@pytest_asyncio.fixture
async def async_session():
    db_file = Path(tempfile.mkdtemp()) / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()
