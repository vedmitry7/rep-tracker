from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.data_export import ExportRequest
from api.app.schemas.data_import import ImportDocument
from api.app.services.data_export import ExportExerciseNotFoundError, export_data
from api.app.services.user import UserBannedError, UserNotFoundError


router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ImportDocument)
async def post_export(
    payload: ExportRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ImportDocument:
    try:
        return await export_data(
            session,
            payload.provider,
            payload.external_id,
            payload.exercise_ids,
        )
    except UserBannedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned") from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from error
    except ExportExerciseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        ) from error
