import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


def _build_engine():
    """Build the async engine — uses Cloud SQL Connector on GCP, direct URL locally."""
    if settings.use_cloud_sql_connector and settings.cloud_sql_instance:
        logger.info(
            "db_using_cloud_sql_connector",
            instance=settings.cloud_sql_instance,
        )
        from google.cloud.sql.connector import Connector

        connector = Connector()

        async def get_conn():
            return await connector.connect_async(
                settings.cloud_sql_instance,
                "asyncpg",
                user=settings.cloud_sql_user,
                password=settings.cloud_sql_password,
                db=settings.cloud_sql_database,
            )

        return create_async_engine(
            "postgresql+asyncpg://",
            async_creator=get_conn,
            echo=settings.debug,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=1800,
        )

    # Local / Docker: use direct connection string
    logger.info("db_using_direct_url")
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


engine = _build_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
