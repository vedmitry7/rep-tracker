from aiogram.types import CallbackQuery, Message

from bot.app.api.client import (
    AccessForbiddenError,
    ApiError,
    BackendUnavailableError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from bot.app.texts import texts


def api_error_text(error: ApiError) -> str:
    if isinstance(error, AccessForbiddenError):
        return texts.ACCESS_FORBIDDEN
    if isinstance(error, BackendUnavailableError):
        return texts.BACKEND_UNAVAILABLE
    if isinstance(error, ResourceNotFoundError):
        return texts.RESOURCE_NOT_FOUND
    if isinstance(error, ResourceConflictError):
        return texts.RESOURCE_CONFLICT
    return texts.REQUEST_FAILED


async def answer_api_error(event: Message | CallbackQuery, error: ApiError) -> None:
    text = api_error_text(error)
    if isinstance(event, CallbackQuery):
        await event.answer(text, show_alert=True)
        return
    await event.answer(text)
