import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Tenant } from "@/lib/types";

export function useMyTenants() {
  return useQuery({
    queryKey: ["tenants", "mine"],
    queryFn: async () => {
      const res = await api.get<Tenant[]>("/tenants/mine");
      return res.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      slug: string;
      name: string;
      description?: string;
    }) => {
      const res = await api.post<Tenant>("/tenants", data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tenants"] }),
  });
}

export function useSwitchTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post<{ ok: boolean; active_tenant_id: string }>(
        `/tenants/switch/${tenantId}`,
      );
      return res.data;
    },
    onSuccess: (_data, tenantId) => {
      if (typeof window !== "undefined") {
        localStorage.setItem("active_tenant_id", tenantId);
      }
      // Tenant scope affects every resource — invalidate all.
      qc.invalidateQueries();
    },
  });
}

export function useAddTenantMember(tenantId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { user_id: string; role?: string }) => {
      const res = await api.post(`/tenants/${tenantId}/members`, data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tenants"] }),
  });
}

export function useRemoveTenantMember(tenantId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/tenants/${tenantId}/members/${userId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tenants"] }),
  });
}
