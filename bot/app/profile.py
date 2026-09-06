from aiogram import Bot


async def configure_profile(bot: Bot) -> None:
    """Configure Telegram-managed localized bot display names."""
    await bot.set_my_name(name="Repka · Workout Tracker")
    await bot.set_my_name(name="Repka · Workout Tracker", language_code="en")
    await bot.set_my_name(name="Репка · Трекер упражнений", language_code="ru")
