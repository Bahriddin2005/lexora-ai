from fastapi import APIRouter

from app.api.v1.admin import misc, words

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(words.router)
router.include_router(misc.router)
