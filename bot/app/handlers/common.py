from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

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


async def edit_or_answer(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    """Edit the current bot UI message, falling back to a new message safely."""

    try:
        await message.edit_text(text, reply_markup=reply_markup)
        return
    except TelegramBadRequest as error:
        if "message is not modified" in str(error).lower():
            return
    except AttributeError:
        # Lightweight test doubles and inaccessible messages use the fallback.
        pass
    await message.answer(text, reply_markup=reply_markup)


async def edit_stored_or_answer(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    chat_id: int | None,
    message_id: int | None,
) -> None:
    """Edit a previously stored UI message after user input, if available."""

    if chat_id is not None and message_id is not None:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
            )
            return
        except TelegramBadRequest as error:
            if "message is not modified" in str(error).lower():
                return
        except AttributeError:
            pass
    await message.answer(text, reply_markup=reply_markup)
