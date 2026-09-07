from aiogram import Bot

from bot.app.texts import available_locales, get_catalog


async def configure_profile(bot: Bot) -> None:
    """Configure Telegram profile copy from the bot's own locale catalogs."""
    default_locale = get_catalog("en")
    await bot.set_my_name(name=default_locale.BOT_NAME)
    await bot.set_my_description(description=default_locale.BOT_DESCRIPTION)
    await bot.set_my_short_description(
        short_description=default_locale.BOT_SHORT_DESCRIPTION
    )
    for locale in available_locales():
        catalog = get_catalog(locale.code)
        await bot.set_my_name(name=catalog.BOT_NAME, language_code=locale.code)
        await bot.set_my_description(
            description=catalog.BOT_DESCRIPTION,
            language_code=locale.code,
        )
        await bot.set_my_short_description(
            short_description=catalog.BOT_SHORT_DESCRIPTION,
            language_code=locale.code,
        )
