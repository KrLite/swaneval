"use client";

import { Loader2, type LucideIcon } from "lucide-react";

interface TableEmptyProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

/**
 * Unified empty-state placeholder for tables and card panels.
 * Use inside <CardContent className="p-0"> so it fills the card.
 */
export function TableEmpty({ icon: Icon, title, description, action }: TableEmptyProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {Icon && (
        <div className="rounded-xl bg-muted p-3 mb-3">
          <Icon className="h-5 w-5 text-muted-foreground/60" />
        </div>
      )}
      <p className="text-sm text-muted-foreground">{title}</p>
      {description && (
        <p className="text-xs text-muted-foreground/60 mt-1 max-w-xs">{description}</p>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

/**
 * Unified loading-state for tables and card panels.
 */
export function TableLoading({ text = "加载中..." }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground mb-2" />
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
