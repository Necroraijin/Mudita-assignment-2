import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.middleware.rate_limit import limiter
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routers import runs

logger = structlog.get_logger()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks: auto-migrate database."""
    settings = get_settings()
    logger.info(
        "app_starting",
        environment=settings.environment,
        cloud_sql=settings.use_cloud_sql_connector,
    )

    # Auto-run migrations on startup (production-safe: Alembic is idempotent)
    if settings.environment in ("production", "staging"):
        try:
            from alembic.config import Config
            from alembic import command
            import os

            alembic_cfg = Config(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
            )
            # Override the DB URL for Alembic with sync URL
            if settings.use_cloud_sql_connector:
                db_url = (
                    f"postgresql+psycopg2://{settings.cloud_sql_user}:"
                    f"{settings.cloud_sql_password}@/{settings.cloud_sql_database}"
                    f"?host=/cloudsql/{settings.cloud_sql_instance}"
                )
                alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            else:
                alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_sync)

            command.upgrade(alembic_cfg, "head")
            logger.info("migrations_applied")
        except Exception as e:
            logger.error("migration_failed", error=str(e))

    yield

    logger.info("app_shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MA2 — Multi-Agent Action Planner",
        description="Three connected mini-agents that process meeting transcripts into reviewed action plans",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Routers
    app.include_router(runs.router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "healthy", "app": settings.app_name}

    return app


app = create_app()
