"""Temporary UI amounts for voluntary Telegram Stars support."""

SUPPORT_PRESET_AMOUNTS: tuple[int, ...] = (5, 25, 100)
SUPPORT_MIN_AMOUNT = 1
SUPPORT_MAX_CUSTOM_AMOUNT = 5_000


def is_valid_support_amount(amount: int) -> bool:
    return SUPPORT_MIN_AMOUNT <= amount <= SUPPORT_MAX_CUSTOM_AMOUNT
