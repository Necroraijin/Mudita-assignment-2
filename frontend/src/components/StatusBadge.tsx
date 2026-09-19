import { Badge } from "./ui/Badge";
import { Spinner } from "./ui/Spinner";

interface StatusBadgeProps {
  status: string;
}

const statusConfig: Record<string, { variant: "default" | "success" | "warning" | "error" | "info"; label: string }> = {
  pending: { variant: "default", label: "Pending" },
  running: { variant: "info", label: "Running" },
  succeeded: { variant: "success", label: "Succeeded" },
  failed: { variant: "error", label: "Failed" },
  needs_review: { variant: "warning", label: "Needs Review" },
  completed_with_issues: { variant: "warning", label: "Completed with Issues" },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || { variant: "default" as const, label: status };

  return (
    <span className="inline-flex items-center gap-1.5">
      {status === "running" && <Spinner size="sm" />}
      <Badge variant={config.variant}>{config.label}</Badge>
    </span>
  );
}
