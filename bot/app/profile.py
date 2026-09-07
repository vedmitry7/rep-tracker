from aiogram import Bot

from bot.app.texts import available_locales, get_catalog


async def configure_profile(bot: Bot) -> None:
    """Apply every profile field; use only from an explicit admin command."""
    await configure_profile_descriptions(bot)
    await configure_profile_names(bot)


async def configure_profile_names(bot: Bot) -> None:
    """Apply localized bot names; Telegram rate-limits these updates."""
    default_locale = get_catalog("en")
    await bot.set_my_name(name=default_locale.BOT_NAME)
    for locale in available_locales():
        catalog = get_catalog(locale.code)
        await bot.set_my_name(name=catalog.BOT_NAME, language_code=locale.code)


async def configure_profile_descriptions(bot: Bot) -> None:
    """Apply localized full and short descriptions from the bot-local catalogs."""
    default_locale = get_catalog("en")
    await bot.set_my_description(description=default_locale.BOT_DESCRIPTION)
    await bot.set_my_short_description(
        short_description=default_locale.BOT_SHORT_DESCRIPTION
    )
    for locale in available_locales():
        catalog = get_catalog(locale.code)
        await bot.set_my_description(
            description=catalog.BOT_DESCRIPTION,
            language_code=locale.code,
        )
        await bot.set_my_short_description(
            short_description=catalog.BOT_SHORT_DESCRIPTION,
            language_code=locale.code,
        )
