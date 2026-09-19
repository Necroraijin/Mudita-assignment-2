import json
import uuid
import structlog
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Run, ContextVersion, AgentOutput, HandoffMessage
from app.agents.graph import compile_graph
from app.services.audit_service import log_action
from app.config import get_settings

logger = structlog.get_logger()


async def get_current_facts(db: AsyncSession, run_id: str) -> list[ContextVersion]:
    """Get the latest version of all facts for a run."""
    result = await db.execute(
        select(ContextVersion)
        .where(
            and_(
                ContextVersion.run_id == uuid.UUID(run_id),
                ContextVersion.superseded_by.is_(None),
            )
        )
        .order_by(ContextVersion.created_at)
    )
    return list(result.scalars().all())


async def update_fact(
    db: AsyncSession, run: Run, fact_id: str, new_value: str
) -> ContextVersion:
    """Update a fact and trigger recomputation of downstream agents."""
    run_id = str(run.id)

    # Find the current version of this fact
    result = await db.execute(
        select(ContextVersion).where(
            and_(
                ContextVersion.id == uuid.UUID(fact_id),
                ContextVersion.run_id == run.id,
                ContextVersion.superseded_by.is_(None),
            )
        )
    )
    old_fact = result.scalar_one_or_none()
    if not old_fact:
        raise ValueError(f"Fact {fact_id} not found or already superseded")

    old_value = old_fact.value

    # Create new version
    new_fact = ContextVersion(
        run_id=run.id,
        fact_key=old_fact.fact_key,
        value=new_value,
        source_reference=old_fact.source_reference,
        category=old_fact.category,
        version=old_fact.version + 1,
    )
    db.add(new_fact)
    await db.flush()

    # Mark old as superseded
    old_fact.superseded_by = new_fact.id
    await db.flush()

    await log_action(
        db, run_id, "user", "fact_corrected",
        f"Fact '{old_fact.fact_key}': '{old_value}' -> '{new_value}'"
    )

    # Trigger recomputation of planning and review
    await recompute_downstream(db, run, old_fact.fact_key)

    return new_fact


async def recompute_downstream(
    db: AsyncSession, run: Run, changed_fact_key: str
) -> None:
    """Recompute planning and review after a fact change."""
    run_id = str(run.id)
    settings = get_settings()

    logger.info("recompute_start", run_id=run_id, changed_fact=changed_fact_key)

    # Get current facts
    current_facts = await get_current_facts(db, run_id)
    facts_data = [
        {
            "fact_id": str(f.id),
            "fact_key": f.fact_key,
            "value": f.value,
            "source_reference": f.source_reference,
            "category": f.category,
        }
        for f in current_facts
    ]

    # Get the latest intake output and update it with corrected facts
    result = await db.execute(
        select(AgentOutput)
        .where(
            and_(
                AgentOutput.run_id == run.id,
                AgentOutput.agent == "intake",
            )
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    intake_output_row = result.scalar_one_or_none()
    if not intake_output_row:
        raise ValueError("No intake output found to base recomputation on")

    # Update intake output with new facts
    updated_intake = dict(intake_output_row.payload_json)
    updated_intake["facts"] = facts_data

    # Update run status
    run.planning_status = "running"
    run.review_status = "pending"
    run.status = "running"
    run.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, run_id, "system", "recompute_started",
        f"Recomputing planning and review due to change in fact '{changed_fact_key}'"
    )

    # Build a partial graph that starts from planning
    graph = compile_graph()

    recompute_state = {
        "run_id": run_id,
        "transcript": run.transcript,
        "rules": run.rules,
        "intake_output": updated_intake,
        "planning_output": None,
        "review_output": None,
        "review_attempt": 0,
        "corrections": [],
        "simulated_failure_at": None,
        "error": None,
        "status": "running",
    }

    # Get latest planning version number
    result = await db.execute(
        select(AgentOutput)
        .where(
            and_(
                AgentOutput.run_id == run.id,
                AgentOutput.agent == "planning",
            )
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    latest_planning = result.scalar_one_or_none()
    base_version = latest_planning.version if latest_planning else 0

    try:
        final_state = recompute_state
        for event in graph.stream(recompute_state):
            for node_name, node_output in event.items():
                final_state = {**final_state, **node_output}

                if node_name == "intake":
                    # Skip intake on recompute — we already have the data
                    continue

                if node_name == "planning":
                    if not final_state.get("error"):
                        planning_data = final_state.get("planning_output", {})
                        new_version = base_version + final_state.get("review_attempt", 0) + 1
                        agent_out = AgentOutput(
                            run_id=run.id,
                            agent="planning",
                            version=new_version,
                            payload_json=planning_data,
                        )
                        db.add(agent_out)
                        run.planning_status = "succeeded"

                        handoff = HandoffMessage(
                            run_id=run.id,
                            from_agent="planning",
                            to_agent="review",
                            content=planning_data,
                        )
                        db.add(handoff)

                elif node_name == "review":
                    if not final_state.get("error"):
                        review_data = final_state.get("review_output", {})
                        agent_out = AgentOutput(
                            run_id=run.id,
                            agent="review",
                            version=base_version + final_state.get("review_attempt", 1),
                            payload_json=review_data,
                        )
                        db.add(agent_out)

                await db.flush()

        # Update final status
        if final_state.get("error"):
            run.status = "failed"
            run.error = final_state["error"]
        elif final_state.get("review_output", {}).get("approved"):
            run.status = "succeeded"
            run.review_status = "succeeded"
        else:
            run.status = "completed_with_issues"
            run.review_status = "succeeded"

        run.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await log_action(db, run_id, "system", "recompute_completed", f"Status: {run.status}")

    except Exception as e:
        logger.error("recompute_error", run_id=run_id, error=str(e))
        run.status = "failed"
        run.error = f"Recomputation failed: {str(e)}"
        run.updated_at = datetime.now(timezone.utc)
        await db.flush()
        raise
