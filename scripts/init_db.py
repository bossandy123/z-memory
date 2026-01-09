import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models import Base, engine
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio

async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_all())
