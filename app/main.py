from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app import models
from app.database import create_db_and_tables
from app.routers.auth import router as auth_router
from app.routers.build import router as builds_router
from app.routers.categories import router as categories_router
from app.routers.me import router as me_router
from app.routers.orders import router as orders_router
from app.routers.parts import router as parts_router
from app.routers.reports import router as reports_router


app = FastAPI(
    title="Hasebty API",
    version="1.0.0",
    description="Backend API for the Hasebty PC Building Service.",
)


app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(parts_router)
app.include_router(builds_router)
app.include_router(me_router)
app.include_router(orders_router)
app.include_router(reports_router)


@app.on_event("startup")
def startup() -> None:
    create_db_and_tables()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "errors": {},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "errors": {},
        },
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Hasebty API",
        version="1.0.0",
        description="Backend API for the Hasebty PC Building Service.",
        routes=app.routes,
    )

    security_schemes = openapi_schema.get("components", {}).get(
        "securitySchemes", {}
    )

    if "OAuth2PasswordBearer" in security_schemes:
        security_schemes["OAuth2PasswordBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def root():
    return {
        "success": True,
        "data": {"message": "Hasebty API is running"},
        "message": "Request completed successfully",
    }