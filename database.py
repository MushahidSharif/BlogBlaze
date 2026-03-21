from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

# DB connection string can be defined in env file. Same exaple dbconnection strings are
# "sqlite+aiosqlite:///./blog.db"
# "postgresql+asyncpg://myuser:mypassword@postgres-db:5432/mydatabase"


SQLALCHEMY_DATABASE_URL = settings.db_connection_string

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    engine = create_async_engine(
         SQLALCHEMY_DATABASE_URL
     )
else:
    # Add support for other database here.
    raise Exception("Unsupported database.")



AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session