"use client";

import { useState } from "react";
import { Card, CardHeader, CardBody } from "./ui/Card";
import { StatusBadge } from "./StatusBadge";
import { Spinner } from "./ui/Spinner";

interface AgentPanelProps {
  title: string;
  status: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function AgentPanel({
  title,
  status,
  children,
  defaultOpen = true,
}: AgentPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Card>
      <CardHeader className="cursor-pointer select-none" >
        <button
          type="button"
          className="flex items-center justify-between w-full"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-ma2-900">{title}</span>
            <StatusBadge status={status} />
          </div>
          <svg
            className={`w-4 h-4 text-ma2-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </CardHeader>
      {isOpen && (
        <CardBody>
          {status === "running" ? (
            <div className="flex items-center gap-2 py-4">
              <Spinner size="sm" />
              <span className="text-sm text-ma2-500">Processing...</span>
            </div>
          ) : status === "pending" ? (
            <p className="text-sm text-ma2-400 py-4">Waiting for previous step to complete.</p>
          ) : (
            children
          )}
        </CardBody>
      )}
    </Card>
  );
}
