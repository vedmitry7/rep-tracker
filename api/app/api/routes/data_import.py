from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.data_import import (
    ImportApplyRequest,
    ImportIdentity,
    ImportPreviewResponse,
    ImportResultResponse,
)
from api.app.services.data_import import (
    ImportDateInFutureError,
    apply_data_import,
    preview_data_import,
)
from api.app.services.user import UserBannedError, UserNotFoundError


router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/preview", response_model=ImportPreviewResponse)
async def post_import_preview(
    payload: ImportIdentity,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ImportPreviewResponse:
    try:
        return await preview_data_import(
            session,
            payload.provider,
            payload.external_id,
            payload.document,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ImportDateInFutureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Import contains a future date",
        ) from error


@router.post("", response_model=ImportResultResponse, status_code=201)
async def post_import(
    payload: ImportApplyRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ImportResultResponse:
    try:
        return await apply_data_import(
            session,
            payload.provider,
            payload.external_id,
            payload.document,
            payload.strategy,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ImportDateInFutureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Import contains a future date",
        ) from error


def _identity_http_error(error: Exception) -> HTTPException:
    if isinstance(error, UserBannedError):
        return HTTPException(status_code=403, detail="User is banned")
    return HTTPException(status_code=404, detail="User not found")
