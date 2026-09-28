import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("lexora")


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


def not_found(message: str = "Topilmadi", **details: Any) -> AppError:
    return AppError(404, "not_found", message, details)


def forbidden(message: str = "Ruxsat yo‘q") -> AppError:
    return AppError(403, "forbidden", message)


def unauthorized(message: str = "Avtorizatsiya talab qilinadi") -> AppError:
    return AppError(401, "unauthorized", message)


def bad_request(message: str, **details: Any) -> AppError:
    return AppError(400, "bad_request", message, details)


def conflict(message: str) -> AppError:
    return AppError(409, "conflict", message)


def ai_unavailable(message: str = "AI xizmati vaqtincha mavjud emas") -> AppError:
    return AppError(503, "ai_unavailable", message)


def _body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "bad_request",
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message, exc.details), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            _body("validation_error", "So‘rov ma’lumotlari noto‘g‘ri", {"errors": errors}), status_code=422
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODES.get(exc.status_code, "error")
        return JSONResponse(_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(_body("internal_error", "Ichki xatolik"), status_code=500)
