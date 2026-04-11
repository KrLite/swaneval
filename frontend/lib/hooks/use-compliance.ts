import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ComplianceRecord, CompliancePolicy } from "@/lib/types";

export function useComplianceRecords(
  resourceType?: "model" | "dataset",
  licenseStatus?: "compliant" | "restricted" | "unknown",
) {
  return useQuery({
    queryKey: ["compliance", "records", resourceType, licenseStatus],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (resourceType) params.resource_type = resourceType;
      if (licenseStatus) params.license_status = licenseStatus;
      const res = await api.get<ComplianceRecord[]>("/compliance/records", {
        params,
      });
      return res.data;
    },
    staleTime: 30_000,
  });
}

export function useCompliancePolicy() {
  return useQuery({
    queryKey: ["compliance", "policy"],
    queryFn: async () => {
      const res = await api.get<CompliancePolicy>("/compliance/policy");
      return res.data;
    },
    staleTime: 5 * 60_000,
  });
}

export function useScanCompliance() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      resource_type: "model" | "dataset";
      resource_id: string;
    }) => {
      const res = await api.post("/compliance/scan", null, { params: data });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["compliance", "records"] });
    },
  });
}
