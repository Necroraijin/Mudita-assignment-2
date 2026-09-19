"use client";

import { Badge } from "./ui/Badge";
import type { PlanningPayload } from "@/lib/types";

interface PlanningViewProps {
  data: PlanningPayload;
}

const typeColors: Record<string, "success" | "info" | "warning"> = {
  fact: "success",
  recommendation: "info",
  open_question: "warning",
};

const priorityColors: Record<string, "error" | "warning" | "default"> = {
  high: "error",
  medium: "warning",
  low: "default",
};

export function PlanningView({ data }: PlanningViewProps) {
  return (
    <div className="space-y-4">
      {/* Tasks Table */}
      <div>
        <h4 className="text-sm font-medium text-ma2-700 mb-2">
          Tasks ({data.tasks.length})
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ma2-200">
                <th className="text-left py-2 px-3 text-xs font-medium text-ma2-500">ID</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-ma2-500">Description</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-ma2-500">Owner</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-ma2-500">Deadline</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-ma2-500">Type</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-ma2-500">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ma2-100">
              {data.tasks.map((task) => (
                <tr key={task.task_id} className="hover:bg-ma2-50">
                  <td className="py-2 px-3 font-mono text-xs text-ma2-400">
                    {task.task_id}
                  </td>
                  <td className="py-2 px-3 text-ma2-800 max-w-md">
                    {task.description}
                    {task.dependencies.length > 0 && (
                      <span className="text-xs text-ma2-400 ml-1">
                        (depends on: {task.dependencies.join(", ")})
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-ma2-700">
                    {task.owner || <span className="text-ma2-300 italic">Unassigned</span>}
                  </td>
                  <td className="py-2 px-3 text-ma2-700">
                    {task.deadline || <span className="text-ma2-300 italic">TBD</span>}
                  </td>
                  <td className="py-2 px-3">
                    <Badge variant={typeColors[task.item_type] || "default"}>
                      {task.item_type.replace("_", " ")}
                    </Badge>
                  </td>
                  <td className="py-2 px-3">
                    <Badge variant={priorityColors[task.priority] || "default"}>
                      {task.priority}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assumptions */}
      {data.assumptions.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">Assumptions</h4>
          <ul className="list-disc list-inside space-y-1">
            {data.assumptions.map((a, i) => (
              <li key={i} className="text-sm text-ma2-600">{a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Open Questions */}
      {data.open_questions.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">Open Questions</h4>
          <ul className="list-disc list-inside space-y-1">
            {data.open_questions.map((q, i) => (
              <li key={i} className="text-sm text-amber-700">{q}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Change Log (from loop iterations) */}
      {data.change_log && data.change_log.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-ma2-700 mb-2">Changes in This Revision</h4>
          <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
            <ul className="list-disc list-inside space-y-1">
              {data.change_log.map((change, i) => (
                <li key={i} className="text-xs text-blue-700">{change}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
