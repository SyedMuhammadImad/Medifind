from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from medifind.api import router
from medifind.config import Settings
from medifind.database import make_engine, readiness
from medifind.search_api import router as search_router


def create_app(settings: Settings | None = None, *, engine: Engine | None = None) -> FastAPI:
    config = settings or Settings()
    owned_engine = engine is None
    database = engine or make_engine(config.database_url.get_secret_value())

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        if owned_engine:
            database.dispose()

    app = FastAPI(title="MEDIFIND", version="0.1.0", lifespan=lifespan)
    app.state.engine = database
    app.state.settings = config
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )
    app.include_router(router)
    app.include_router(search_router)

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(HTTPException)
    async def http_error(_request, error):
        return JSONResponse({"error": error.detail}, status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, _error):
        # Never echo request inputs (including passwords) or validator exception context.
        return JSONResponse(
            {"error": {"code": "validation_error", "message": "Invalid request"}}, status_code=422
        )

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(_request, _error):
        return JSONResponse(
            {"error": {"code": "storage_unavailable", "message": "Storage unavailable"}},
            status_code=503,
        )

    @app.get("/health/live")
    def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    def ready():
        status = readiness(database)
        return JSONResponse({"status": status}, status_code=200 if status == "ready" else 503)

    return app
