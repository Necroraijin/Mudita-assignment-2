"use client";

import Link from "next/link";
import { Card, CardHeader, CardBody } from "./ui/Card";
import { StatusBadge } from "./StatusBadge";
import { Spinner } from "./ui/Spinner";
import { useRuns } from "@/hooks/useRuns";

export function RunList() {
  const { runs, error, isLoading } = useRuns();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
        Failed to load runs: {error}
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <Card>
        <CardBody>
          <div className="text-center py-8">
            <p className="text-ma2-500 text-sm">No runs yet.</p>
            <Link
              href="/runs/new"
              className="mt-2 inline-block text-sm text-ma2-700 hover:text-ma2-900 underline"
            >
              Create your first run
            </Link>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold text-ma2-900">All Runs</h2>
      </CardHeader>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-ma2-100">
              <th className="px-6 py-3 text-left text-xs font-medium text-ma2-500 uppercase tracking-wider">
                Run ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ma2-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ma2-500 uppercase tracking-wider">
                Intake
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ma2-500 uppercase tracking-wider">
                Planning
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ma2-500 uppercase tracking-wider">
                Review
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ma2-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ma2-100">
            {runs.map((run) => (
              <tr key={run.id} className="hover:bg-ma2-50 transition-colors">
                <td className="px-6 py-4">
                  <Link
                    href={`/runs/${run.id}`}
                    className="text-sm font-mono text-ma2-700 hover:text-ma2-900 underline"
                  >
                    {run.id.slice(0, 8)}...
                  </Link>
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={run.status} />
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={run.intake_status} />
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={run.planning_status} />
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={run.review_status} />
                </td>
                <td className="px-6 py-4 text-sm text-ma2-500">
                  {new Date(run.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
