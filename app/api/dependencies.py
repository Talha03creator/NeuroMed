"""
API Dependencies
Agentic Clinical Intelligence Platform

FastAPI dependencies for injection into route handlers.
"""

from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for SQLAlchemy database connections.
    Provides an async database session and ensures proper cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
