import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Run
from app.services.audit_service import log_action

logger = structlog.get_logger()


async def simulate_failure(db: AsyncSession, run: Run, step: str) -> None:
    """Inject a simulated failure at a specific step."""
    run_id = str(run.id)

    run.simulated_failure_at = step
    run.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, run_id, "user", "simulate_failure",
        f"[simulated fault] Failure injected at step: {step}"
    )

    logger.info("failure_injected", run_id=run_id, step=step)
