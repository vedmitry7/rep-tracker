from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.api.router import api_router
from api.app.db.session import get_db_session


app = FastAPI(title="Rep Tracker API")
app.include_router(api_router)


@app.get("/health/db")
async def database_health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"database": "ok"}
