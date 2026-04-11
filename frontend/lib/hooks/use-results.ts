import { useQuery, keepPreviousData } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  EvalResult,
  LeaderboardEntry,
  TaskSummaryEntry,
  PaginatedResponse,
  ThroughputPoint,
  VersionComparisonRow,
  EloRankingRow,
} from "@/lib/types";

export function useResults(taskId?: string, page = 1, pageSize = 50, enabled = true) {
  return useQuery({
    queryKey: ["results", taskId, page, pageSize],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (taskId) params.task_id = taskId;
      const res = await api.get<PaginatedResponse<EvalResult>>("/results", { params });
      return res.data;
    },
    enabled,
    staleTime: 10_000,
    placeholderData: keepPreviousData,
  });
}

export function useLeaderboard(criterionId?: string) {
  return useQuery({
    queryKey: ["leaderboard", criterionId],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (criterionId) params.criterion_id = criterionId;
      const res = await api.get<LeaderboardEntry[]>("/results/leaderboard", { params });
      return res.data;
    },
    staleTime: 30_000,
  });
}

export function useTaskSummary(taskId: string, refetchInterval?: number | false) {
  return useQuery({
    queryKey: ["results", "summary", taskId],
    queryFn: async () => {
      const res = await api.get<
        { criteria: TaskSummaryEntry[]; error_count: number } | TaskSummaryEntry[]
      >("/results/summary", {
        params: { task_id: taskId },
      });
      // Backend returns {criteria: [...], error_count} — normalize
      const data = res.data;
      if (Array.isArray(data)) return data;
      return data.criteria ?? [];
    },
    enabled: !!taskId,
    refetchInterval,
  });
}

export function useErrorResults(taskId: string, page = 1, pageSize = 50, refetchInterval?: number | false) {
  return useQuery({
    queryKey: ["results", "errors-paginated", taskId, page, pageSize],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<EvalResult>>("/results/errors", {
        params: { task_id: taskId, page, page_size: pageSize },
      });
      return res.data;
    },
    enabled: !!taskId,
    refetchInterval,
    placeholderData: keepPreviousData,
  });
}

export function useThroughput(taskIds: string[]) {
  return useQuery({
    queryKey: ["results", "throughput", taskIds.slice().sort().join(",")],
    queryFn: async () => {
      if (!taskIds.length) return [];
      const params = new URLSearchParams();
      for (const id of taskIds) params.append("task_ids", id);
      const res = await api.get<ThroughputPoint[]>("/results/throughput", {
        params,
      });
      return res.data;
    },
    enabled: taskIds.length > 0,
    staleTime: 30_000,
  });
}

export function useVersionComparison(baseModelId: string, criterionId?: string) {
  return useQuery({
    queryKey: ["results", "version-comparison", baseModelId, criterionId],
    queryFn: async () => {
      const params: Record<string, string> = { base_model_id: baseModelId };
      if (criterionId) params.criterion_id = criterionId;
      const res = await api.get<VersionComparisonRow[]>(
        "/results/version-comparison",
        { params },
      );
      return res.data;
    },
    enabled: !!baseModelId,
    staleTime: 30_000,
  });
}

export function useEloRanking(taskId: string, criterionId: string) {
  return useQuery({
    queryKey: ["results", "elo-ranking", taskId, criterionId],
    queryFn: async () => {
      const res = await api.get<EloRankingRow[]>("/results/elo-ranking", {
        params: { task_id: taskId, criterion_id: criterionId },
      });
      return res.data;
    },
    enabled: !!taskId && !!criterionId,
    staleTime: 30_000,
  });
}

export function useErrorAnalysis(taskId: string, errorOnly: boolean = false) {
  return useQuery({
    queryKey: ["results", "errors-analysis", taskId, errorOnly],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<EvalResult>>("/results/errors", {
        params: { task_id: taskId, error_only: errorOnly, page_size: 50 },
      });
      return res.data;
    },
    enabled: !!taskId,
  });
}
