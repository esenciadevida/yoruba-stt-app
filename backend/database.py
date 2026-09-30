from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW

engine = create_async_engine(
    DATABASE_URL, echo=False, pool_pre_ping=True,
    pool_size=DB_POOL_SIZE, max_overflow=DB_MAX_OVERFLOW, pool_timeout=30,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Every index below is already declared in the models' __table_args__,
        # so create_all creates them. Re-creating them here only ever failed
        # with "already exists", and on Postgres a failed statement aborts the
        # whole transaction, which made engine.begin() roll back the schema
        # that create_all had just built. So they are not repeated here.
        #
        # Columns added after v2.0 still need an ALTER on databases created
        # before they existed (create_all does not add columns to a table that
        # already exists). Fresh databases get them from the models, and
        # TINYINT(1) is MySQL-only, so this is MySQL-gated. Each statement runs
        # in a savepoint so one failure cannot abort the surrounding
        # transaction, and the guard makes re-running init_db safe.
        if engine.dialect.name == "mysql":
            for col_sql in [
                "ALTER TABLE transcriptions ADD COLUMN original_filename VARCHAR(255) NULL",
                "ALTER TABLE transcriptions ADD COLUMN title VARCHAR(200) NULL",
                "ALTER TABLE transcriptions ADD COLUMN pinned TINYINT(1) NOT NULL DEFAULT 0",
            ]:
                try:
                    async with conn.begin_nested():
                        await conn.execute(text(col_sql))
                except Exception:
                    pass
