import json
import uuid
import structlog
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Run, ContextVersion, AgentOutput, HandoffMessage, ReviewCycle
from app.agents.graph import compile_graph
from app.services.audit_service import log_action
from app.schemas.intake import IntakeOutput
from app.config import get_settings

logger = structlog.get_logger()


async def create_run(db: AsyncSession, transcript: str, rules: str) -> Run:
    run = Run(
        transcript=transcript,
        rules=rules,
        status="pending",
    )
    db.add(run)
    await db.flush()
    await log_action(db, str(run.id), "system", "run_created", "New run initialized")
    return run


async def list_runs(db: AsyncSession) -> list[Run]:
    result = await db.execute(
        select(Run).order_by(Run.created_at.desc())
    )
    return list(result.scalars().all())


async def get_run(db: AsyncSession, run_id: str) -> Run | None:
    result = await db.execute(
        select(Run)
        .where(Run.id == uuid.UUID(run_id))
        .options(
            selectinload(Run.context_versions),
            selectinload(Run.agent_outputs),
            selectinload(Run.handoff_messages),
            selectinload(Run.review_cycles),
            selectinload(Run.action_logs),
        )
    )
    return result.scalar_one_or_none()


async def execute_run(db: AsyncSession, run: Run) -> None:
    """Execute the full agent pipeline for a run."""
    settings = get_settings()
    run_id = str(run.id)

    run.status = "running"
    run.intake_status = "running"
    await db.flush()
    await log_action(db, run_id, "system", "run_started", "Pipeline execution started")

    try:
        graph = compile_graph()

        initial_state = {
            "run_id": run_id,
            "transcript": run.transcript,
            "rules": run.rules,
            "intake_output": None,
            "planning_output": None,
            "review_output": None,
            "review_attempt": 0,
            "corrections": [],
            "simulated_failure_at": run.simulated_failure_at,
            "error": None,
            "status": "running",
            # Loop engineering state
            "correction_history": [],
            "loop_iterations": [],
            "previous_plans": [],
            "planning_change_log": [],
            "convergence_stalled": False,
        }

        final_state = initial_state

        for event in graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = {**final_state, **node_output}

                if node_name == "intake":
                    if final_state.get("error"):
                        run.intake_status = "failed"
                        run.error = final_state["error"]
                    else:
                        run.intake_status = "succeeded"
                        run.planning_status = "running"

                        intake_data = final_state.get("intake_output", {})
                        agent_out = AgentOutput(
                            run_id=run.id,
                            agent="intake",
                            version=1,
                            payload_json=intake_data,
                        )
                        db.add(agent_out)

                        for fact in intake_data.get("facts", []):
                            cv = ContextVersion(
                                run_id=run.id,
                                fact_key=fact.get("fact_key", ""),
                                value=fact.get("value", ""),
                                source_reference=fact.get("source_reference", ""),
                                category=fact.get("category", "decision"),
                                version=1,
                            )
                            db.add(cv)

                        handoff = HandoffMessage(
                            run_id=run.id,
                            from_agent="intake",
                            to_agent="planning",
                            content=intake_data,
                        )
                        db.add(handoff)

                        await log_action(
                            db, run_id, "intake", "output_produced",
                            f"Extracted {len(intake_data.get('facts', []))} facts"
                        )

                elif node_name == "planning":
                    if final_state.get("error"):
                        run.planning_status = "failed"
                        run.error = final_state["error"]
                    else:
                        run.planning_status = "succeeded"
                        run.review_status = "running"

                        planning_data = final_state.get("planning_output", {})
                        version = final_state.get("review_attempt", 0) + 1

                        agent_out = AgentOutput(
                            run_id=run.id,
                            agent="planning",
                            version=version,
                            payload_json=planning_data,
                        )
                        db.add(agent_out)

                        handoff = HandoffMessage(
                            run_id=run.id,
                            from_agent="planning",
                            to_agent="review",
                            content=planning_data,
                        )
                        db.add(handoff)

                        # Log change details
                        change_log = planning_data.get("change_log", [])
                        changes_detail = "; ".join(change_log) if change_log else "Initial plan"
                        await log_action(
                            db, run_id, "planning", "output_produced",
                            f"Created {len(planning_data.get('tasks', []))} tasks (v{version}). Changes: {changes_detail[:300]}"
                        )

                elif node_name == "review":
                    review_data = final_state.get("review_output", {})
                    attempt = final_state.get("review_attempt", 1)

                    if final_state.get("error"):
                        run.review_status = "failed"
                        run.error = final_state["error"]
                    else:
                        approved = review_data.get("approved", False)

                        # Include loop telemetry in the agent output
                        review_payload = {
                            **review_data,
                            "_loop_telemetry": {
                                "attempt": attempt,
                                "correction_history": final_state.get("correction_history", []),
                                "convergence_stalled": final_state.get("convergence_stalled", False),
                            },
                        }

                        agent_out = AgentOutput(
                            run_id=run.id,
                            agent="review",
                            version=attempt,
                            payload_json=review_payload,
                        )
                        db.add(agent_out)

                        # Store loop iteration data in review cycle
                        loop_iterations = final_state.get("loop_iterations", [])
                        current_iteration = loop_iterations[-1] if loop_iterations else {}

                        cycle = ReviewCycle(
                            run_id=run.id,
                            attempt_number=attempt,
                            corrections={
                                "corrections": review_data.get("corrections", []),
                                "resolved_from_previous": review_data.get("resolved_from_previous", []),
                                "loop_telemetry": current_iteration,
                            },
                            resolved=approved,
                        )
                        db.add(cycle)

                        if not approved and attempt < settings.max_review_cycles:
                            stalled = final_state.get("convergence_stalled", False)
                            if stalled:
                                run.review_status = "succeeded"
                                await log_action(
                                    db, run_id, "review", "convergence_stalled",
                                    f"Attempt {attempt}: Loop stalled — corrections not decreasing. Stopping early."
                                )
                            else:
                                run.review_status = "needs_review"
                                run.planning_status = "running"

                                handoff = HandoffMessage(
                                    run_id=run.id,
                                    from_agent="review",
                                    to_agent="planning",
                                    content=review_data,
                                )
                                db.add(handoff)

                                # Log detailed loop progress
                                resolved_count = len(review_data.get("resolved_from_previous", []))
                                corrections_count = len(review_data.get("corrections", []))
                                history = final_state.get("correction_history", [])
                                open_count = len([h for h in history if h.get("status") in ("open", "persistent", "regressed")])
                                total_resolved = len([h for h in history if h.get("status") == "resolved"])

                                await log_action(
                                    db, run_id, "review", "corrections_sent",
                                    f"Attempt {attempt}: {corrections_count} corrections ({resolved_count} resolved this round). "
                                    f"Cumulative: {total_resolved} resolved, {open_count} open."
                                )
                        elif approved:
                            run.review_status = "succeeded"
                            history = final_state.get("correction_history", [])
                            total_resolved = len([h for h in history if h.get("status") == "resolved"])
                            await log_action(
                                db, run_id, "review", "plan_approved",
                                f"Plan approved on attempt {attempt}. Total corrections resolved: {total_resolved}"
                            )
                        else:
                            run.review_status = "succeeded"
                            history = final_state.get("correction_history", [])
                            persistent = [h for h in history if h.get("status") in ("persistent", "regressed")]
                            await log_action(
                                db, run_id, "review", "cap_reached",
                                f"Review cap reached after {attempt} attempts. "
                                f"{len(persistent)} persistent/regressed issues remain."
                            )

                    run.review_attempt = attempt

                await db.flush()

        # Set final run status
        if final_state.get("error"):
            run.status = "failed"
            run.error = final_state["error"]
        elif final_state.get("review_output", {}).get("approved"):
            run.status = "succeeded"
        else:
            review_output = final_state.get("review_output", {})
            history = final_state.get("correction_history", [])
            unresolved = [h for h in history if h.get("status") in ("open", "persistent", "regressed")]
            if unresolved or review_output.get("corrections"):
                run.status = "completed_with_issues"
            else:
                run.status = "succeeded"

        run.updated_at = datetime.now(timezone.utc)
        await db.flush()

        # Final summary log
        loop_iterations = final_state.get("loop_iterations", [])
        total_tokens = sum(
            it.get("planning_tokens_in", 0) + it.get("planning_tokens_out", 0)
            + it.get("review_tokens_in", 0) + it.get("review_tokens_out", 0)
            for it in loop_iterations
        )
        await log_action(
            db, run_id, "system", "run_completed",
            f"Final status: {run.status}. "
            f"Loop iterations: {len(loop_iterations)}. "
            f"Loop tokens: {total_tokens}. "
            f"Convergence stalled: {final_state.get('convergence_stalled', False)}"
        )

    except Exception as e:
        logger.error("run_execution_error", run_id=run_id, error=str(e))
        run.status = "failed"
        run.error = str(e)
        run.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await log_action(db, run_id, "system", "run_error", f"Error: {str(e)[:500]}")
        raise


async def reset_run(db: AsyncSession, run: Run) -> None:
    run_id = str(run.id)

    run.status = "pending"
    run.intake_status = "pending"
    run.planning_status = "pending"
    run.review_status = "pending"
    run.review_attempt = 0
    run.simulated_failure_at = None
    run.error = None
    run.updated_at = datetime.now(timezone.utc)

    for cv in run.context_versions:
        await db.delete(cv)
    for ao in run.agent_outputs:
        await db.delete(ao)
    for hm in run.handoff_messages:
        await db.delete(hm)
    for rc in run.review_cycles:
        await db.delete(rc)

    await db.flush()
    await log_action(db, run_id, "system", "run_reset", "Run reset to initial state")
