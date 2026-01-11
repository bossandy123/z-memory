import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models import Base, engine
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio

async def create_all():
    print("Creating database tables...")
    print(f"Found {len(Base.metadata.tables)} tables to create:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("\nDatabase tables created successfully!")
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  ✓ {table_name}")

if __name__ == "__main__":
    asyncio.run(create_all())
