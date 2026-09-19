"use client";

import { Card, CardHeader, CardBody } from "./ui/Card";
import { Badge } from "./ui/Badge";
import type { IntakePayload } from "@/lib/types";

interface IntakeViewProps {
  data: IntakePayload;
}

const categoryColors: Record<string, "info" | "success" | "warning"> = {
  decision: "info",
  requirement: "success",
  constraint: "warning",
};

const severityColors: Record<string, "error" | "warning" | "info"> = {
  blocking: "error",
  warning: "warning",
  info: "info",
};

export function IntakeView({ data }: IntakeViewProps) {
  return (
    <div className="space-y-4">
      {/* Facts */}
      <div>
        <h4 className="text-sm font-medium text-ma2-700 mb-2">
          Extracted Facts ({data.facts.length})
        </h4>
        <div className="space-y-2">
          {data.facts.map((fact) => (
            <div
              key={fact.fact_id}
              className="rounded-lg border border-ma2-200 bg-ma2-50 px-4 py-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-ma2-400">{fact.fact_id}</span>
                    <Badge variant={categoryColors[fact.category] || "default"}>
                      {fact.category}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium text-ma2-900">{fact.fact_key}</p>
                  <p className="text-sm text-ma2-700 mt-0.5">{fact.value}</p>
                  <p className="text-xs text-ma2-400 mt-1 italic">
                    Source: &ldquo;{fact.source_reference}&rdquo;
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Gaps */}
      {data.gaps.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">
            Gaps ({data.gaps.length})
          </h4>
          <div className="space-y-2">
            {data.gaps.map((gap, i) => (
              <div
                key={i}
                className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3"
              >
                <div className="flex items-start gap-2">
                  <Badge variant={severityColors[gap.severity] || "warning"}>
                    {gap.severity}
                  </Badge>
                  <p className="text-sm text-ma2-800">{gap.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflicts */}
      {data.conflicts.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">
            Conflicts ({data.conflicts.length})
          </h4>
          <div className="space-y-2">
            {data.conflicts.map((conflict, i) => (
              <div
                key={i}
                className="rounded-lg border border-red-200 bg-red-50 px-4 py-3"
              >
                <p className="text-sm text-red-800">{conflict}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
