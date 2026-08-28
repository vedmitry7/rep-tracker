from bot.app.handlers.exercises import router as exercises_router
from bot.app.handlers.history import router as history_router
from bot.app.handlers.results import router as results_router
from bot.app.handlers.settings import router as settings_router
from bot.app.handlers.start import router as start_router

__all__ = [
    "exercises_router",
    "history_router",
    "results_router",
    "settings_router",
    "start_router",
]
