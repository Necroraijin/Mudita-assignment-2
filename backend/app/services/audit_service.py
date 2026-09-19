import re
import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.action_log import ActionLog

logger = structlog.get_logger()

SECRET_PATTERN = re.compile(
    r"(AIza[a-zA-Z0-9\-_]{35}|Bearer\s+[a-zA-Z0-9\-_.]+|password\s*[=:]\s*\S+)",
    re.IGNORECASE,
)


def strip_secrets_from_detail(detail: str) -> str:
    return SECRET_PATTERN.sub("[REDACTED]", detail)


async def log_action(
    db: AsyncSession,
    run_id: str,
    actor: str,
    action: str,
    detail: str = "",
) -> None:
    sanitized_detail = strip_secrets_from_detail(detail)

    entry = ActionLog(
        run_id=run_id,
        actor=actor,
        action=action,
        detail=sanitized_detail,
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "action_logged",
        run_id=run_id,
        actor=actor,
        action=action,
        detail_preview=sanitized_detail[:200],
    )
