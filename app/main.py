from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import create_db_and_tables
from app.routers.auth import router as auth_router
from app.routers.build import router as builds_router
from app.routers.categories import router as categories_router
from app.routers.me import router as me_router
from app.routers.orders import router as orders_router
from app.routers.parts import router as parts_router
from app.routers.reports import router as reports_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(
    title="Hasebty API",
    version="1.0.0",
    description="Backend API for the Hasebty PC Building Service.",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(parts_router)
app.include_router(builds_router)
app.include_router(me_router)
app.include_router(orders_router)
app.include_router(reports_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Also covers FastAPI's own HTTPException and unknown URLs (404).
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(exc.detail), "errors": {}},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Turn pydantic's list of problems into { "field": "what is wrong" }.
    errors: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in ("body", "query", "path")]
        errors[".".join(location) or "request"] = str(error["msg"])

    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"success": False, "message": "Validation failed", "errors": errors}
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "errors": {}},
    )


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Hasebty API",
        version="1.0.0",
        description="Backend API for the Hasebty PC Building Service.",
        routes=app.routes,
    )

    security_schemes = openapi_schema.get("components", {}).get("securitySchemes", {})

    if "OAuth2PasswordBearer" in security_schemes:
        security_schemes["OAuth2PasswordBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "success": True,
        "data": {"message": "Hasebty API is running"},
        "message": "Request completed successfully",
    }
