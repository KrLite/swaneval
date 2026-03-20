"use client";

import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

interface SelectionBarProps {
  count: number;
  onDelete: () => void;
  onClear: () => void;
}

export function SelectionBar({ count, onDelete, onClear }: SelectionBarProps) {
  if (count === 0) return null;

  return (
    <div className="fixed bottom-6 left-0 right-0 z-30 flex justify-center pointer-events-none animate-float-up">
      <div className="pointer-events-auto flex items-center gap-3 bg-muted border rounded-full px-5 py-2.5 text-sm shadow-lg">
        <span className="text-muted-foreground">
          已选择{" "}
          <span className="font-semibold text-foreground tabular-nums">
            {count}
          </span>{" "}
          项
        </span>
        <Button
          size="sm"
          variant="destructive"
          className="h-7 rounded-full text-xs"
          onClick={onDelete}
        >
          <Trash2 className="mr-1 h-3 w-3" />
          删除
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 rounded-full text-xs"
          onClick={onClear}
        >
          取消
        </Button>
      </div>
    </div>
  );
}
