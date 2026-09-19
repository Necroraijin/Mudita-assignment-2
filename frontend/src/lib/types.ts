export interface RunListItem {
  id: string;
  status: string;
  intake_status: string;
  planning_status: string;
  review_status: string;
  created_at: string;
}

export interface AgentOutput {
  agent: string;
  version: number;
  payload_json: Record<string, unknown>;
  tokens_in: number | null;
  tokens_out: number | null;
  latency_ms: number | null;
  created_at: string;
}

export interface HandoffMessage {
  from_agent: string;
  to_agent: string;
  content: Record<string, unknown>;
  created_at: string;
}

export interface ReviewCycle {
  attempt_number: number;
  corrections: Record<string, unknown>;
  resolved: boolean;
  created_at: string;
}

export interface ActionLog {
  actor: string;
  action: string;
  detail: string;
  created_at: string;
}

export interface Fact {
  id: string;
  fact_key: string;
  value: string;
  source_reference: string;
  category: string;
  version: number;
  created_at: string;
}

export interface RunDetail {
  id: string;
  transcript: string;
  rules: string;
  status: string;
  intake_status: string;
  planning_status: string;
  review_status: string;
  review_attempt: number;
  error: string | null;
  created_at: string;
  updated_at: string;
  agent_outputs: AgentOutput[];
  handoff_messages: HandoffMessage[];
  review_cycles: ReviewCycle[];
  action_logs: ActionLog[];
  facts: Fact[];
}

export interface SourceFact {
  fact_id: string;
  fact_key: string;
  value: string;
  source_reference: string;
  category: "decision" | "requirement" | "constraint";
}

export interface Gap {
  description: string;
  severity: "blocking" | "warning" | "info";
}

export interface IntakePayload {
  facts: SourceFact[];
  gaps: Gap[];
  conflicts: string[];
}

export interface TaskItem {
  task_id: string;
  description: string;
  owner: string | null;
  deadline: string | null;
  dependencies: string[];
  source_fact_ids: string[];
  item_type: "fact" | "recommendation" | "open_question";
  priority: "high" | "medium" | "low";
}

export interface PlanningPayload {
  tasks: TaskItem[];
  assumptions: string[];
  open_questions: string[];
  change_log: string[];
}

export interface ReviewCorrection {
  issue: string;
  evidence: string;
  required_change: string;
  related_task_ids: string[];
  severity: "critical" | "major" | "minor";
  is_new: boolean;
}

export interface ReviewPayload {
  approved: boolean;
  corrections: ReviewCorrection[];
  resolved_from_previous: string[];
  unresolved_issues: string[];
  summary: string;
}
