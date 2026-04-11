"use client";

import { useEffect, useState } from "react";
import { Building2, Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useMyTenants, useSwitchTenant } from "@/lib/hooks/use-tenants";

export function TenantSwitcher() {
  const { data: tenants = [] } = useMyTenants();
  const switchTenant = useSwitchTenant();
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("active_tenant_id");
      if (stored) {
        setActiveId(stored);
        return;
      }
    }
    if (tenants.length > 0 && !activeId) {
      setActiveId(tenants[0].id);
    }
  }, [tenants, activeId]);

  if (tenants.length === 0) {
    return null;
  }

  const handleSwitch = async (tenantId: string) => {
    setActiveId(tenantId);
    try {
      await switchTenant.mutateAsync(tenantId);
    } catch {
      // revert on failure
      const stored = localStorage.getItem("active_tenant_id");
      setActiveId(stored || tenants[0].id);
    }
  };

  const active = tenants.find((t) => t.id === activeId) ?? tenants[0];

  if (tenants.length === 1) {
    return (
      <div className="hidden md:flex items-center gap-1.5 text-xs text-muted-foreground px-2">
        <Building2 className="h-3.5 w-3.5" />
        <span>{active.name}</span>
      </div>
    );
  }

  return (
    <Select value={activeId} onValueChange={handleSwitch}>
      <SelectTrigger className="hidden md:flex h-8 w-auto gap-1.5 text-xs">
        <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
        <SelectValue placeholder="选择租户">
          {active.name}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {tenants.map((t) => (
          <SelectItem key={t.id} value={t.id}>
            <div className="flex items-center gap-2">
              <span>{t.name}</span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {t.slug}
              </span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
