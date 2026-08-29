from fastapi import APIRouter

from api.app.api.routes.exercise_entries import router as exercise_entries_router
from api.app.api.routes.exercises import router as exercises_router
from api.app.api.routes.data_import import router as data_import_router
from api.app.api.routes.users import router as users_router


api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(exercises_router)
api_router.include_router(exercise_entries_router)
api_router.include_router(data_import_router)
