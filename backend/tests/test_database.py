from app.database import Base, db_session_factory, engine


def test_database_configuration_is_available() -> None:
    assert engine.url.render_as_string(hide_password=False).startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://"))
    assert Base is not None
    assert db_session_factory is not None
