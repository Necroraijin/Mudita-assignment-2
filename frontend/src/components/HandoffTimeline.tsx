"use client";

import { Badge } from "./ui/Badge";
import type { HandoffMessage } from "@/lib/types";

interface HandoffTimelineProps {
  messages: HandoffMessage[];
}

const agentColors: Record<string, "info" | "success" | "warning"> = {
  intake: "info",
  planning: "success",
  review: "warning",
};

export function HandoffTimeline({ messages }: HandoffTimelineProps) {
  if (messages.length === 0) return null;

  return (
    <div>
      <h4 className="text-sm font-medium text-ma2-700 mb-3">Handoff Timeline</h4>
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-ma2-200" />
        <div className="space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className="relative pl-10">
              <div className="absolute left-2.5 top-1.5 w-3 h-3 rounded-full bg-ma2-400 border-2 border-white" />
              <div className="rounded-lg border border-ma2-200 bg-white px-4 py-2">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={agentColors[msg.from_agent] || "default"}>
                    {msg.from_agent}
                  </Badge>
                  <span className="text-xs text-ma2-400">-&gt;</span>
                  <Badge variant={agentColors[msg.to_agent] || "default"}>
                    {msg.to_agent}
                  </Badge>
                  <span className="text-xs text-ma2-300 ml-auto">
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-ma2-500 truncate">
                  {JSON.stringify(msg.content).slice(0, 120)}...
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
