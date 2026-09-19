import asyncio
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, async_session_factory
from app.schemas.run import (
    RunCreate,
    RunListItem,
    RunDetailResponse,
    AgentOutputResponse,
    HandoffMessageResponse,
    ReviewCycleResponse,
    ActionLogResponse,
    FactResponse,
    FactUpdateRequest,
    SimulateFailureRequest,
)
from app.services import run_service, fact_service, failure_service

logger = structlog.get_logger()
router = APIRouter(prefix="/runs", tags=["runs"])


async def run_pipeline_background(run_id: str):
    """Execute the pipeline in background with its own DB session."""
    async with async_session_factory() as db:
        try:
            run = await run_service.get_run(db, run_id)
            if run:
                await run_service.execute_run(db, run)
                await db.commit()
        except Exception as e:
            logger.error("background_pipeline_error", run_id=run_id, error=str(e))
            await db.rollback()


@router.post("", status_code=201)
async def create_run(
    body: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    run = await run_service.create_run(db, body.transcript, body.rules)
    await db.commit()

    # Start pipeline in background
    background_tasks.add_task(run_pipeline_background, str(run.id))

    return {"id": str(run.id), "status": run.status}


@router.get("")
async def list_runs(db: AsyncSession = Depends(get_db)):
    runs = await run_service.list_runs(db)
    return [
        RunListItem(
            id=str(r.id),
            status=r.status,
            intake_status=r.intake_status,
            planning_status=r.planning_status,
            review_status=r.review_status,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get current (non-superseded) facts
    current_facts = await fact_service.get_current_facts(db, run_id)

    return RunDetailResponse(
        id=str(run.id),
        transcript=run.transcript,
        rules=run.rules,
        status=run.status,
        intake_status=run.intake_status,
        planning_status=run.planning_status,
        review_status=run.review_status,
        review_attempt=run.review_attempt,
        error=run.error,
        created_at=run.created_at,
        updated_at=run.updated_at,
        agent_outputs=[
            AgentOutputResponse(
                agent=ao.agent,
                version=ao.version,
                payload_json=ao.payload_json,
                tokens_in=ao.tokens_in,
                tokens_out=ao.tokens_out,
                latency_ms=ao.latency_ms,
                created_at=ao.created_at,
            )
            for ao in sorted(run.agent_outputs, key=lambda x: x.created_at)
        ],
        handoff_messages=[
            HandoffMessageResponse(
                from_agent=hm.from_agent,
                to_agent=hm.to_agent,
                content=hm.content,
                created_at=hm.created_at,
            )
            for hm in sorted(run.handoff_messages, key=lambda x: x.created_at)
        ],
        review_cycles=[
            ReviewCycleResponse(
                attempt_number=rc.attempt_number,
                corrections=rc.corrections,
                resolved=rc.resolved,
                created_at=rc.created_at,
            )
            for rc in sorted(run.review_cycles, key=lambda x: x.attempt_number)
        ],
        action_logs=[
            ActionLogResponse(
                actor=al.actor,
                action=al.action,
                detail=al.detail,
                created_at=al.created_at,
            )
            for al in sorted(run.action_logs, key=lambda x: x.created_at)
        ],
        facts=[
            FactResponse(
                id=str(f.id),
                fact_key=f.fact_key,
                value=f.value,
                source_reference=f.source_reference,
                category=f.category,
                version=f.version,
                created_at=f.created_at,
            )
            for f in current_facts
        ],
    )


@router.post("/{run_id}/facts/{fact_id}")
async def update_fact(
    run_id: str,
    fact_id: str,
    body: FactUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    run = await run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        new_fact = await fact_service.update_fact(db, run, fact_id, body.value)
        await db.commit()
        return {
            "id": str(new_fact.id),
            "fact_key": new_fact.fact_key,
            "value": new_fact.value,
            "version": new_fact.version,
            "status": "recomputing",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/reset")
async def reset_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    await run_service.reset_run(db, run)
    return {"id": str(run.id), "status": "pending"}


@router.post("/{run_id}/simulate-failure")
async def simulate_failure(
    run_id: str,
    body: SimulateFailureRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    run = await run_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    await failure_service.simulate_failure(db, run, body.step)

    # Re-execute the run with the failure injected
    background_tasks.add_task(run_pipeline_background, str(run.id))

    return {
        "id": str(run.id),
        "simulated_failure_at": body.step,
        "status": "running",
    }
