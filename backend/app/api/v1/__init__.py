from fastapi import APIRouter

from app.api.v1 import auth, discover, languages, me, reports, search, translate, words
from app.api.v1.admin import router as admin_router

api_router = APIRouter()
for module in (auth, languages, search, words, discover, translate, me, reports):
    api_router.include_router(module.router)
api_router.include_router(admin_router)
