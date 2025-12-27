import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route
from sqlalchemy import select

async def list_routes():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Route))
        routes = result.scalars().all()
        print(f"Found {len(routes)} routes:")
        for r in routes:
            print(f"ID: {r.id}, Title: '{r.title}'")

if __name__ == "__main__":
    asyncio.run(list_routes())
