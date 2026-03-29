"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useClusters } from "@/lib/hooks/use-clusters";

interface ClusterSelectProps {
  value: string;
  onValueChange: (value: string) => void;
}

export function ClusterSelect({ value, onValueChange }: ClusterSelectProps) {
  const { data: clusters = [] } = useClusters();

  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger><SelectValue placeholder="选择集群" /></SelectTrigger>
      <SelectContent>
        {clusters.length === 0 ? (
          <div className="px-3 py-4 text-center text-xs text-muted-foreground">
            暂无集群，<a href="/clusters" className="text-primary hover:underline">去添加</a>
          </div>
        ) : clusters.map((c) => (
          <SelectItem key={c.id} value={c.id}>
            {c.name}
            <span className="text-muted-foreground ml-1">
              {c.gpu_count > 0 ? `${c.gpu_count} GPU` : "CPU"}
              {c.gpu_type ? ` (${c.gpu_type})` : ""}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
