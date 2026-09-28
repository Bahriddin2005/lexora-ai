import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import settings
from app.core.db import SessionLocal
from app.core.errors import install_error_handlers
from app.core.redis import get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lexora AI API",
        version="0.1.0",
        description="Dictionary + Translator + AI + Learning + Live Language Database",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/healthz", tags=["system"])
    async def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["system"])
    async def readyz():
        checks = {"db": False, "redis": False}
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["db"] = True
        except Exception:  # noqa: BLE001
            pass
        try:
            checks["redis"] = bool(await get_redis().ping())
        except Exception:  # noqa: BLE001
            pass
        ok = all(checks.values())
        return JSONResponse({"status": "ok" if ok else "degraded", **checks}, status_code=200 if ok else 503)

    return app


app = create_app()
