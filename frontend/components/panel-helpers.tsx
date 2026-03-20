import * as React from "react";
import { Label } from "@/components/ui/label";

export function PanelField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">
        {label}
        {required && <span className="text-destructive ml-0.5">*</span>}
      </Label>
      {children}
    </div>
  );
}

export function DetailRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline gap-2 text-xs">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <div className="flex-1 border-b border-dashed border-muted-foreground/20 min-w-4 translate-y-[-3px]" />
      <div className="text-right shrink-0 min-w-0">{value}</div>
    </div>
  );
}
