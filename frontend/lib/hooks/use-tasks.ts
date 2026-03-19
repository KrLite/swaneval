import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { EvalSubtask, EvalTask } from "@/lib/types";

export function useTasks(status?: string) {
  return useQuery({
    queryKey: ["tasks", status],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (status) params.status_filter = status;
      const res = await api.get<EvalTask[]>("/tasks", { params });
      return res.data;
    },
    refetchInterval: 5000,
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ["tasks", id],
    queryFn: async () => {
      const res = await api.get<EvalTask>(`/tasks/${id}`);
      return res.data;
    },
    enabled: !!id,
    refetchInterval: 3000,
  });
}

export function useSubtasks(taskId: string) {
  return useQuery({
    queryKey: ["tasks", taskId, "subtasks"],
    queryFn: async () => {
      const res = await api.get<EvalSubtask[]>(`/tasks/${taskId}/subtasks`);
      return res.data;
    },
    enabled: !!taskId,
    refetchInterval: 3000,
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      name: string;
      model_id: string;
      dataset_ids: string[];
      criteria_ids: string[];
      params_json?: string;
      repeat_count?: number;
      seed_strategy?: string;
      gpu_ids?: string;
      env_vars?: string;
    }) => {
      const res = await api.post<EvalTask>("/tasks", data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function usePauseTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post<EvalTask>(`/tasks/${id}/pause`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useResumeTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post<EvalTask>(`/tasks/${id}/resume`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useCancelTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post<EvalTask>(`/tasks/${id}/cancel`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/tasks/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["results"] });
      qc.invalidateQueries({ queryKey: ["leaderboard"] });
    },
  });
}
