"use client";

import { Badge } from "./ui/Badge";
import type { ReviewPayload, ReviewCycle } from "@/lib/types";

interface ReviewViewProps {
  data: ReviewPayload;
  cycles: ReviewCycle[];
}

const severityColors: Record<string, "error" | "warning" | "info"> = {
  critical: "error",
  major: "warning",
  minor: "info",
};

interface LoopTelemetry {
  attempt: number;
  corrections_raised: number;
  corrections_resolved: number;
  corrections_new: number;
  corrections_regressed: number;
  planning_tokens_in: number;
  planning_tokens_out: number;
  review_tokens_in: number;
  review_tokens_out: number;
}

interface CycleCorrections {
  corrections: Array<{
    issue: string;
    required_change: string;
    severity?: string;
    is_new?: boolean;
  }>;
  resolved_from_previous?: string[];
  loop_telemetry?: LoopTelemetry;
}

export function ReviewView({ data, cycles }: ReviewViewProps) {
  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="rounded-lg border border-ma2-200 bg-ma2-50 px-4 py-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-ma2-700">Verdict:</span>
          <Badge variant={data.approved ? "success" : "warning"}>
            {data.approved ? "Approved" : "Needs Corrections"}
          </Badge>
        </div>
        <p className="text-sm text-ma2-600">{data.summary}</p>
      </div>

      {/* Resolved from previous (loop progress) */}
      {data.resolved_from_previous && data.resolved_from_previous.length > 0 && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
          <h4 className="text-sm font-medium text-emerald-700 mb-1">
            Resolved This Round ({data.resolved_from_previous.length})
          </h4>
          <ul className="list-disc list-inside space-y-0.5">
            {data.resolved_from_previous.map((issue, i) => (
              <li key={i} className="text-xs text-emerald-600">{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Loop Telemetry */}
      {cycles.length > 1 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">
            Loop Progress
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {cycles.map((cycle) => {
              const corr = cycle.corrections as unknown as CycleCorrections | null;
              const telemetry = corr?.loop_telemetry;
              if (!telemetry) return null;
              return (
                <div
                  key={cycle.attempt_number}
                  className="rounded-lg border border-ma2-200 bg-white px-3 py-2 text-center"
                >
                  <p className="text-xs text-ma2-400 mb-1">Attempt {telemetry.attempt}</p>
                  <div className="flex justify-center gap-3 text-xs">
                    <span className="text-red-600" title="Raised">
                      {telemetry.corrections_raised} raised
                    </span>
                    <span className="text-emerald-600" title="Resolved">
                      {telemetry.corrections_resolved} fixed
                    </span>
                  </div>
                  {telemetry.corrections_regressed > 0 && (
                    <p className="text-xs text-amber-600 mt-0.5">
                      {telemetry.corrections_regressed} regressed
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Review Cycles */}
      {cycles.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">
            Review Cycles ({cycles.length})
          </h4>
          <div className="space-y-2">
            {cycles.map((cycle) => {
              const corr = cycle.corrections as unknown as CycleCorrections | null;
              const corrections = corr?.corrections || [];
              const resolved = corr?.resolved_from_previous || [];

              return (
                <div
                  key={cycle.attempt_number}
                  className={`rounded-lg border px-4 py-3 ${
                    cycle.resolved
                      ? "border-emerald-200 bg-emerald-50"
                      : "border-amber-200 bg-amber-50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">
                      Attempt {cycle.attempt_number}
                    </span>
                    <div className="flex items-center gap-2">
                      {resolved.length > 0 && (
                        <span className="text-xs text-emerald-600">
                          {resolved.length} resolved
                        </span>
                      )}
                      <Badge variant={cycle.resolved ? "success" : "warning"}>
                        {cycle.resolved ? "Approved" : "Sent Back"}
                      </Badge>
                    </div>
                  </div>
                  {corrections.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {corrections.map((c, i) => (
                        <li key={i} className="text-xs text-ma2-600 flex items-start gap-1.5">
                          {c.severity && (
                            <Badge variant={severityColors[c.severity] || "warning"} className="mt-0.5 shrink-0">
                              {c.severity}
                            </Badge>
                          )}
                          <span>
                            <span className="font-medium">{c.issue}</span>
                            {" — "}
                            {c.required_change}
                            {c.is_new === false && (
                              <span className="text-amber-500 ml-1">(recurring)</span>
                            )}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Current Corrections */}
      {data.corrections.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">
            Current Corrections ({data.corrections.length})
          </h4>
          <div className="space-y-2">
            {data.corrections.map((correction, i) => (
              <div
                key={i}
                className={`rounded-lg border px-4 py-3 ${
                  correction.severity === "critical"
                    ? "border-red-300 bg-red-50"
                    : correction.severity === "minor"
                    ? "border-blue-200 bg-blue-50"
                    : "border-amber-200 bg-amber-50"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={severityColors[correction.severity || "major"] || "warning"}>
                    {correction.severity || "major"}
                  </Badge>
                  {correction.is_new === false && (
                    <Badge variant="warning">recurring</Badge>
                  )}
                </div>
                <p className="text-sm font-medium text-ma2-800">
                  {correction.issue}
                </p>
                <p className="text-xs text-ma2-500 mt-1">
                  Evidence: &ldquo;{correction.evidence}&rdquo;
                </p>
                <p className="text-xs text-ma2-700 mt-1 font-medium">
                  Required change: {correction.required_change}
                </p>
                {correction.related_task_ids.length > 0 && (
                  <p className="text-xs text-ma2-400 mt-1">
                    Affects: {correction.related_task_ids.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unresolved Issues */}
      {data.unresolved_issues.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-red-700 mb-2">
            Unresolved Issues
          </h4>
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
            <ul className="list-disc list-inside space-y-1">
              {data.unresolved_issues.map((issue, i) => (
                <li key={i} className="text-sm text-red-700">{issue}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
