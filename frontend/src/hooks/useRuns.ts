"use client";

import { useCallback } from "react";
import { listRuns } from "@/lib/api";
import { usePolling } from "./usePolling";
import type { RunListItem } from "@/lib/types";

export function useRuns() {
  const fetcher = useCallback(() => listRuns(), []);

  const { data, error, isLoading, refetch } = usePolling<RunListItem[]>(
    fetcher,
    5000,
    true,
  );

  return {
    runs: data || [],
    error,
    isLoading,
    refetch,
  };
}
