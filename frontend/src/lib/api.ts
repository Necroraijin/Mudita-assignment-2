import { API_BASE_URL } from "./constants";
import type { RunListItem, RunDetail } from "./types";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  return res.json();
}

export async function createRun(
  transcript: string,
  rules: string,
): Promise<{ id: string; status: string }> {
  return fetchApi("/runs", {
    method: "POST",
    body: JSON.stringify({ transcript, rules }),
  });
}

export async function listRuns(): Promise<RunListItem[]> {
  return fetchApi("/runs");
}

export async function getRun(id: string): Promise<RunDetail> {
  return fetchApi(`/runs/${id}`);
}

export async function updateFact(
  runId: string,
  factId: string,
  value: string,
): Promise<{ id: string; fact_key: string; value: string; version: number }> {
  return fetchApi(`/runs/${runId}/facts/${factId}`, {
    method: "POST",
    body: JSON.stringify({ value }),
  });
}

export async function resetRun(
  runId: string,
): Promise<{ id: string; status: string }> {
  return fetchApi(`/runs/${runId}/reset`, { method: "POST" });
}

export async function simulateFailure(
  runId: string,
  step: string,
): Promise<{ id: string; simulated_failure_at: string; status: string }> {
  return fetchApi(`/runs/${runId}/simulate-failure`, {
    method: "POST",
    body: JSON.stringify({ step }),
  });
}
