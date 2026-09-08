"""Configuration and validation for voluntary Telegram Stars support.

Change the temporary preset values and the custom amount limit here when the
product values are decided. Both the bot and API deliberately use this module.
"""

SUPPORT_PRESET_AMOUNTS: tuple[int, ...] = (5, 25, 100)
SUPPORT_MIN_AMOUNT = 1
SUPPORT_MAX_CUSTOM_AMOUNT = 5_000
SUPPORT_INVOICE_TTL_HOURS = 24


def is_valid_support_amount(amount: int) -> bool:
    return SUPPORT_MIN_AMOUNT <= amount <= SUPPORT_MAX_CUSTOM_AMOUNT
