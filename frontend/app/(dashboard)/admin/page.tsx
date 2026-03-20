"use client";

import { useState, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Trash2,
  Search,
  ArrowUpDown,
  ShieldCheck,
  ShieldOff,
  Users,
} from "lucide-react";
import { TableEmpty, TableLoading } from "@/components/table-states";
import { useUsers, useUpdateUser, useDeleteUser } from "@/lib/hooks/use-users";
import { DeleteDialog } from "@/components/delete-dialog";
import { FilterDropdown } from "@/components/filter-dropdown";
import { TablePagination } from "@/components/table-pagination";
import type { User } from "@/lib/types";


const roleLabel: Record<string, string> = {
  admin: "管理员",
  data_admin: "数据管理员",
  engineer: "工程师",
  viewer: "观察者",
};

const roleBadgeVariant: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  admin: "default",
  data_admin: "secondary",
  engineer: "outline",
  viewer: "outline",
};

export default function AdminPage() {
  const { data: users = [], isLoading } = useUsers();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const [deleteTarget, setDeleteTarget] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [deleteError, setDeleteError] = useState("");
  const [globalFilter, setGlobalFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("__all__");
  const [sorting, setSorting] = useState<SortingState>([]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteError("");
    try {
      await deleteUser.mutateAsync(deleteTarget.id);
      setDeleteTarget(null);
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response
              ?.data?.detail
          : undefined;
      setDeleteError(detail || "删除失败");
    }
  };

  const handleToggleActive = async (user: User) => {
    if (user.role === "admin") return;
    await updateUser.mutateAsync({
      id: user.id,
      is_active: !user.is_active,
    });
  };

  const handleRoleChange = async (user: User, newRole: string) => {
    if (user.role === "admin") return;
    await updateUser.mutateAsync({
      id: user.id,
      role: newRole,
    });
  };

  const filteredData = useMemo(
    () =>
      roleFilter === "__all__"
        ? users
        : users.filter((u) => u.role === roleFilter),
    [users, roleFilter],
  );

  const roleCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const u of users) {
      counts[u.role] = (counts[u.role] || 0) + 1;
    }
    return counts;
  }, [users]);

  const columns = useMemo<ColumnDef<User>[]>(
    () => [
      {
        accessorKey: "username",
        header: "用户名",
        cell: ({ getValue }) => (
          <span className="font-medium">{getValue<string>()}</span>
        ),
      },
      {
        accessorKey: "nickname",
        header: "昵称",
        cell: ({ getValue }) => (
          <span className="text-muted-foreground">
            {getValue<string>() || "—"}
          </span>
        ),
      },
      {
        accessorKey: "email",
        header: "邮箱",
        cell: ({ getValue }) => (
          <span className="text-muted-foreground text-sm">
            {getValue<string>()}
          </span>
        ),
      },
      {
        accessorKey: "role",
        header: "角色",
        cell: ({ row }) => {
          const user = row.original;
          if (user.role === "admin") {
            return (
              <Badge variant={roleBadgeVariant[user.role]}>
                {roleLabel[user.role]}
              </Badge>
            );
          }
          return (
            <Select
              value={user.role}
              onValueChange={(v) => handleRoleChange(user, v)}
            >
              <SelectTrigger className="h-7 w-[120px] text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="data_admin">数据管理员</SelectItem>
                <SelectItem value="engineer">工程师</SelectItem>
                <SelectItem value="viewer">观察者</SelectItem>
              </SelectContent>
            </Select>
          );
        },
      },
      {
        accessorKey: "is_active",
        header: "状态",
        cell: ({ row }) => {
          const user = row.original;
          return (
            <Badge
              variant={user.is_active ? "outline" : "destructive"}
              className="font-normal"
            >
              {user.is_active ? "活跃" : "已禁用"}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const user = row.original;
          if (user.role === "admin") {
            return (
              <span className="text-xs text-muted-foreground/50">受保护</span>
            );
          }
          return (
            <div className="flex items-center justify-end gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                title={user.is_active ? "禁用账号" : "启用账号"}
                onClick={() => handleToggleActive(user)}
              >
                {user.is_active ? (
                  <ShieldOff className="h-3.5 w-3.5 text-muted-foreground" />
                ) : (
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                title="删除用户"
                onClick={() =>
                  setDeleteTarget({
                    id: user.id,
                    name: user.username,
                  })
                }
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          );
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 20 } },
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center gap-5">
          <h1 className="text-lg font-semibold">用户管理</h1>
          <div className="hidden sm:flex items-center gap-4 text-xs text-muted-foreground">
            <span>
              共{" "}
              <span className="font-semibold text-foreground tabular-nums">
                {users.length}
              </span>{" "}
              个用户
            </span>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          管理系统用户账号、角色和权限。管理员可以修改用户角色、禁用账号或删除用户。
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="搜索用户名、邮箱..."
            className="pl-9 h-8 rounded-full text-xs"
          />
        </div>
        <FilterDropdown
          label="角色"
          options={Object.entries(roleCounts).map(([role, count]) => ({
            key: role,
            label: roleLabel[role] ?? role,
            count,
          }))}
          value={roleFilter}
          onChange={setRoleFilter}
        />
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <TableLoading />
          ) : table.getRowModel().rows.length === 0 ? (
            (users ?? []).length === 0 ? (
              <TableEmpty
                icon={Users}
                title="暂无用户"
              />
            ) : (
              <TableEmpty title="无匹配结果" />
            )
          ) : (
            <>
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((hg) => (
                    <TableRow key={hg.id}>
                      {hg.headers.map((header) => (
                        <TableHead
                          key={header.id}
                          className={
                            header.column.getCanSort()
                              ? "cursor-pointer select-none"
                              : ""
                          }
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <span className="flex items-center gap-1">
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext(),
                            )}
                            {header.column.getCanSort() && (
                              <ArrowUpDown className="h-3 w-3 text-muted-foreground/50" />
                            )}
                          </span>
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {table.getRowModel().rows.map((row) => (
                    <TableRow key={row.id}>
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id} className="py-2.5">
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext(),
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <TablePagination table={table} />
            </>
          )}
        </CardContent>
      </Card>

      {/* Delete confirmation */}
      <DeleteDialog
        open={!!deleteTarget}
        title="删除用户"
        name={deleteTarget?.name ?? ""}
        error={deleteError}
        isPending={deleteUser.isPending}
        onConfirm={handleDelete}
        onCancel={() => {
          setDeleteTarget(null);
          setDeleteError("");
        }}
      />
    </div>
  );
}
