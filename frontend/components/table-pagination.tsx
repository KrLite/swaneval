"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Table } from "@tanstack/react-table";

interface TablePaginationProps<T> {
  table: Table<T>;
}

export function TablePagination<T>({ table }: TablePaginationProps<T>) {
  const pageIndex = table.getState().pagination.pageIndex;
  const pageCount = table.getPageCount();
  const totalRows = table.getFilteredRowModel().rows.length;

  if (totalRows <= table.getState().pagination.pageSize) return null;

  return (
    <div className="flex items-center justify-center gap-2 py-3 border-t">
      <Button
        size="sm"
        variant="outline"
        className="h-7 w-7 p-0"
        disabled={!table.getCanPreviousPage()}
        onClick={() => table.previousPage()}
      >
        <ChevronLeft className="h-3.5 w-3.5" />
      </Button>
      <span className="text-xs text-muted-foreground px-2">
        <span className="font-semibold text-foreground tabular-nums">
          {pageIndex + 1}
        </span>
        {" / "}
        <span className="tabular-nums">{pageCount}</span>
        <span className="ml-2 text-muted-foreground">
          共 {totalRows} 条
        </span>
      </span>
      <Button
        size="sm"
        variant="outline"
        className="h-7 w-7 p-0"
        disabled={!table.getCanNextPage()}
        onClick={() => table.nextPage()}
      >
        <ChevronRight className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
