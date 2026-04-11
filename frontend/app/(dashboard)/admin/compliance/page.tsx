"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { useComplianceRecords, useCompliancePolicy } from "@/lib/hooks/use-compliance";
import { formatTime } from "@/lib/time";

export default function CompliancePage() {
  const [resourceFilter, setResourceFilter] = useState<string>("__all__");
  const [statusFilter, setStatusFilter] = useState<string>("__all__");

  const { data: records = [], isLoading } = useComplianceRecords(
    resourceFilter === "__all__"
      ? undefined
      : (resourceFilter as "model" | "dataset"),
    statusFilter === "__all__"
      ? undefined
      : (statusFilter as "compliant" | "restricted" | "unknown"),
  );
  const { data: policy } = useCompliancePolicy();

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">合规审计</h1>
        <p className="text-sm text-muted-foreground mt-1">
          模型与数据集的 License 状态和 CVE 发现。License 自动从 HuggingFace /
          ModelScope cardData 解析，CVE 扫描需要集群节点安装 trivy。
        </p>
      </div>

      <div className="flex gap-3">
        <Select value={resourceFilter} onValueChange={setResourceFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="资源类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部资源</SelectItem>
            <SelectItem value="model">模型</SelectItem>
            <SelectItem value="dataset">数据集</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="合规状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部状态</SelectItem>
            <SelectItem value="compliant">合规</SelectItem>
            <SelectItem value="restricted">受限</SelectItem>
            <SelectItem value="unknown">未知</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">合规记录</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="p-4 text-xs text-muted-foreground">加载中...</p>
          ) : records.length === 0 ? (
            <p className="p-4 text-xs text-muted-foreground">
              暂无合规记录。前往模型或数据集详情页点击&ldquo;扫描合规性&rdquo;触发第一次审计。
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>资源类型</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>License</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>CVE</TableHead>
                  <TableHead>上次扫描</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {records.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>
                      <Badge variant="outline" className="text-[10px]">
                        {r.resource_type === "model" ? "模型" : "数据集"}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {r.resource_name || r.resource_id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {r.license_spdx || "—"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          r.license_status === "compliant"
                            ? "success"
                            : r.license_status === "restricted"
                              ? "destructive"
                              : "outline"
                        }
                        className="text-[10px]"
                      >
                        {r.license_status === "compliant"
                          ? "合规"
                          : r.license_status === "restricted"
                            ? "受限"
                            : "未知"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {r.cve_findings.length === 0 ? (
                        <span className="text-[11px] text-muted-foreground">
                          无
                        </span>
                      ) : (
                        <Badge variant="outline" className="text-[10px]">
                          {r.cve_findings.length} 项
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-[11px] text-muted-foreground">
                      {formatTime(r.last_scanned_at) ?? "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {policy && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">License 策略</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs font-medium mb-1.5">合规 License</p>
              <div className="flex flex-wrap gap-1">
                {policy.compliant.map((l) => (
                  <Badge
                    key={l}
                    variant="outline"
                    className="text-[10px] font-mono"
                  >
                    {l}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">受限 License</p>
              <div className="flex flex-wrap gap-1">
                {policy.restricted.map((l) => (
                  <Badge
                    key={l}
                    variant="outline"
                    className="text-[10px] font-mono"
                  >
                    {l}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
