import asyncio
import os
from app.database.session import engine, Base
from app.models.report import MedicalReport

async def init():
    async with engine.begin() as conn:
        print("Dropping tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database recreated successfully.")

if __name__ == "__main__":
    if os.path.exists("neuromed_clinical.db"):
        print("Removing db file...")
        try:
            os.remove("neuromed_clinical.db")
        except Exception as e:
            print(f"Could not remove: {e}")
    asyncio.run(init())
