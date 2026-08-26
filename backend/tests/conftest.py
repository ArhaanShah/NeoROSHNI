from __future__ import annotations

import os
from pathlib import Path

# Use a local SQLite file DB for test execution when DATABASE_URL is not explicitly set in env
BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DB_PATH = BASE_DIR / "test_neoroshni.db"

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}")

from collections.abc import AsyncGenerator  # noqa: E402

import pytest_asyncio  # noqa: E402

from app.database import Base, engine  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def pytest_sessionfinish(session, exitstatus):
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass
