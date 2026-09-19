"use client";

import { useState } from "react";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { updateFact } from "@/lib/api";
import type { Fact } from "@/lib/types";

interface FactEditorProps {
  runId: string;
  facts: Fact[];
  onFactUpdated: () => void;
}

export function FactEditor({ runId, facts, onFactUpdated }: FactEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEdit = (fact: Fact) => {
    setEditingId(fact.id);
    setEditValue(fact.value);
    setError(null);
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditValue("");
    setError(null);
  };

  const handleSave = async (factId: string) => {
    if (!editValue.trim()) {
      setError("Value cannot be empty");
      return;
    }

    setIsUpdating(true);
    setError(null);

    try {
      await updateFact(runId, factId, editValue);
      setEditingId(null);
      setEditValue("");
      onFactUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update fact");
    } finally {
      setIsUpdating(false);
    }
  };

  if (facts.length === 0) {
    return (
      <p className="text-sm text-ma2-400 italic">No facts extracted yet.</p>
    );
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-ma2-700">
        Source Facts ({facts.length})
      </h4>
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      )}
      <div className="space-y-2">
        {facts.map((fact) => (
          <div
            key={fact.id}
            className="rounded-lg border border-ma2-200 bg-white px-4 py-3"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-ma2-400">{fact.fact_key}</span>
                <Badge variant="default">v{fact.version}</Badge>
              </div>
              {editingId !== fact.id && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleEdit(fact)}
                >
                  Edit
                </Button>
              )}
            </div>

            {editingId === fact.id ? (
              <div className="mt-2 space-y-2">
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full rounded-md border border-ma2-300 px-3 py-1.5 text-sm focus:border-ma2-500 focus:outline-none focus:ring-1 focus:ring-ma2-500"
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleSave(fact.id)}
                    disabled={isUpdating}
                  >
                    {isUpdating ? "Saving..." : "Save & Recompute"}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCancel}
                    disabled={isUpdating}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-ma2-800">{fact.value}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
