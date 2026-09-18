from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.centers import router as centers_router
from app.api.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(centers_router)
api_router.include_router(chat_router)

__all__ = ["api_router"]
