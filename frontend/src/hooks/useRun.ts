"use client";

import { useCallback, useMemo } from "react";
import { getRun } from "@/lib/api";
import { usePolling } from "./usePolling";
import { POLLING_INTERVAL_MS } from "@/lib/constants";
import type { RunDetail } from "@/lib/types";

export function useRun(runId: string) {
  const fetcher = useCallback(() => getRun(runId), [runId]);

  const { data, error, isLoading, refetch } = usePolling<RunDetail>(
    fetcher,
    POLLING_INTERVAL_MS,
    true,
  );

  const shouldPoll = useMemo(() => {
    if (!data) return true;
    return data.status === "running" || data.status === "pending";
  }, [data]);

  // Re-create polling with updated shouldPoll
  const fetcherForPolling = useCallback(() => getRun(runId), [runId]);
  const result = usePolling<RunDetail>(
    fetcherForPolling,
    POLLING_INTERVAL_MS,
    shouldPoll,
  );

  return {
    run: result.data,
    error: result.error,
    isLoading: result.isLoading,
    refetch: result.refetch,
  };
}
