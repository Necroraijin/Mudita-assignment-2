"use client";

import { useState } from "react";
import { Button } from "./ui/Button";
import { StatusBadge } from "./StatusBadge";
import { AgentPanel } from "./AgentPanel";
import { IntakeView } from "./IntakeView";
import { PlanningView } from "./PlanningView";
import { ReviewView } from "./ReviewView";
import { FactEditor } from "./FactEditor";
import { HandoffTimeline } from "./HandoffTimeline";
import { Spinner } from "./ui/Spinner";
import { useRun } from "@/hooks/useRun";
import { resetRun, simulateFailure } from "@/lib/api";
import type {
  IntakePayload,
  PlanningPayload,
  ReviewPayload,
} from "@/lib/types";

interface RunDetailProps {
  runId: string;
}

export function RunDetail({ runId }: RunDetailProps) {
  const { run, error, isLoading, refetch } = useRun(runId);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [simulatingStep, setSimulatingStep] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
        {error || "Run not found"}
      </div>
    );
  }

  // Extract latest outputs per agent
  const intakeOutputs = run.agent_outputs.filter((o) => o.agent === "intake");
  const planningOutputs = run.agent_outputs.filter((o) => o.agent === "planning");
  const reviewOutputs = run.agent_outputs.filter((o) => o.agent === "review");

  const latestIntake = intakeOutputs.length > 0
    ? (intakeOutputs[intakeOutputs.length - 1].payload_json as unknown as IntakePayload)
    : null;
  const latestPlanning = planningOutputs.length > 0
    ? (planningOutputs[planningOutputs.length - 1].payload_json as unknown as PlanningPayload)
    : null;
  const latestReview = reviewOutputs.length > 0
    ? (reviewOutputs[reviewOutputs.length - 1].payload_json as unknown as ReviewPayload)
    : null;

  const handleReset = async () => {
    setIsResetting(true);
    setActionError(null);
    try {
      await resetRun(runId);
      refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to reset");
    } finally {
      setIsResetting(false);
    }
  };

  const handleSimulateFailure = async (step: string) => {
    setSimulatingStep(step);
    setActionError(null);
    try {
      await simulateFailure(runId, step);
      refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to simulate");
    } finally {
      setSimulatingStep(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-ma2-900">Run Detail</h1>
          <p className="text-sm font-mono text-ma2-400 mt-1">{run.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={run.status} />
        </div>
      </div>

      {/* Error banner */}
      {run.error && (
        <div className={`rounded-lg border px-4 py-3 text-sm ${
          run.error.includes("[simulated fault]")
            ? "bg-amber-50 border-amber-300 text-amber-800"
            : "bg-red-50 border-red-200 text-red-700"
        }`}>
          {run.error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleReset}
          disabled={isResetting}
        >
          {isResetting ? "Resetting..." : "Reset Run"}
        </Button>
        <span className="text-xs text-ma2-400 mx-1">Simulate failure at:</span>
        {["intake", "planning", "review"].map((step) => (
          <Button
            key={step}
            variant="ghost"
            size="sm"
            onClick={() => handleSimulateFailure(step)}
            disabled={simulatingStep !== null}
          >
            {simulatingStep === step ? "Injecting..." : step}
          </Button>
        ))}
      </div>

      {actionError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      )}

      {/* Agent Panels */}
      <div className="space-y-4">
        <AgentPanel title="1. Intake Agent" status={run.intake_status}>
          {latestIntake ? (
            <IntakeView data={latestIntake} />
          ) : (
            <p className="text-sm text-ma2-400">No output yet.</p>
          )}
        </AgentPanel>

        <AgentPanel title="2. Planning Agent" status={run.planning_status}>
          {latestPlanning ? (
            <PlanningView data={latestPlanning} />
          ) : (
            <p className="text-sm text-ma2-400">No output yet.</p>
          )}
        </AgentPanel>

        <AgentPanel title="3. Review Agent" status={run.review_status}>
          {latestReview ? (
            <ReviewView data={latestReview} cycles={run.review_cycles} />
          ) : (
            <p className="text-sm text-ma2-400">No output yet.</p>
          )}
        </AgentPanel>
      </div>

      {/* Fact Editor */}
      {run.facts.length > 0 && (
        <div className="border-t border-ma2-200 pt-6">
          <FactEditor
            runId={runId}
            facts={run.facts}
            onFactUpdated={refetch}
          />
        </div>
      )}

      {/* Handoff Timeline */}
      {run.handoff_messages.length > 0 && (
        <div className="border-t border-ma2-200 pt-6">
          <HandoffTimeline messages={run.handoff_messages} />
        </div>
      )}

      {/* Action Log */}
      {run.action_logs.length > 0 && (
        <div className="border-t border-ma2-200 pt-6">
          <h4 className="text-sm font-medium text-ma2-700 mb-3">Audit Log</h4>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {run.action_logs.map((log, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="text-ma2-300 font-mono whitespace-nowrap">
                  {new Date(log.created_at).toLocaleTimeString()}
                </span>
                <span className="text-ma2-500 font-medium min-w-[60px]">
                  {log.actor}
                </span>
                <span className="text-ma2-400">{log.action}</span>
                <span className="text-ma2-300 truncate">{log.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
