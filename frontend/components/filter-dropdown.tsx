"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Search, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FilterOption {
  key: string;
  label: string;
  count?: number;
}

interface FilterDropdownProps {
  label: string;
  options: FilterOption[];
  value: string;            // "__all__" or a single key
  onChange: (key: string) => void;
  className?: string;
}

export function FilterDropdown({
  label,
  options,
  value,
  onChange,
  className,
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const activeOption = options.find((o) => o.key === value);
  const displayLabel = activeOption ? activeOption.label : "全部";

  const filtered = search
    ? options.filter((o) =>
        o.label.toLowerCase().includes(search.toLowerCase()),
      )
    : options;

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => { setOpen(!open); setSearch(""); }}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-3 h-8 text-xs font-medium transition-colors",
          value !== "__all__"
            ? "bg-primary/10 border-primary/30 text-primary"
            : "bg-muted border-border text-muted-foreground hover:text-foreground",
        )}
      >
        <span>{label}</span>
        {value !== "__all__" && (
          <>
            <span className="w-px h-3 bg-primary/20" />
            <span className="font-semibold text-foreground max-w-[120px] truncate">
              {displayLabel}
            </span>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onChange("__all__"); }}
              className="rounded-full hover:bg-primary/20 p-0.5 -mr-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </>
        )}
        {value === "__all__" && (
          <ChevronDown className={cn(
            "h-3 w-3 transition-transform",
            open && "rotate-180",
          )} />
        )}
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 min-w-[200px] rounded-xl border bg-card text-foreground shadow-lg overflow-hidden animate-modal-expand"
          style={{ transformOrigin: "top left" }}
        >
          {/* Search */}
          {options.length > 5 && (
            <div className="p-2 border-b">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="搜索..."
                  className="w-full h-8 pl-8 pr-3 text-xs rounded-md border border-border bg-muted outline-none focus:ring-1 focus:ring-primary"
                  autoFocus
                />
              </div>
            </div>
          )}

          {/* Options */}
          <div className="max-h-60 overflow-auto p-1">
            {/* "All" option */}
            <button
              type="button"
              onClick={() => { onChange("__all__"); setOpen(false); setSearch(""); }}
              className={cn(
                "w-full flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors",
                value === "__all__"
                  ? "bg-muted text-foreground"
                  : "hover:bg-muted/50",
              )}
            >
              <Check className={cn("h-3 w-3 shrink-0", value !== "__all__" && "invisible")} />
              <span>全部</span>
            </button>

            {filtered.map((option) => (
              <button
                key={option.key}
                type="button"
                onClick={() => {
                  onChange(value === option.key ? "__all__" : option.key);
                  setOpen(false);
                  setSearch("");
                }}
                className={cn(
                  "w-full flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors",
                  value === option.key
                    ? "bg-muted text-foreground"
                    : "hover:bg-muted/50",
                )}
              >
                <Check className={cn("h-3 w-3 shrink-0", value !== option.key && "invisible")} />
                <span className="flex-1 text-left truncate">{option.label}</span>
                {option.count !== undefined && (
                  <span className="tabular-nums text-muted-foreground">{option.count}</span>
                )}
              </button>
            ))}

            {filtered.length === 0 && (
              <p className="px-2.5 py-3 text-xs text-muted-foreground text-center">
                无匹配项
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
