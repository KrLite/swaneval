"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useVersionComparison } from "@/lib/hooks/use-results";
import type { VersionComparisonRow } from "@/lib/types";

const LINE_COLORS = [
  "#7C3AED",
  "#2563EB",
  "#059669",
  "#DC2626",
  "#D97706",
  "#DB2777",
];

type ChartPoint = {
  version: string;
  [criterionName: string]: number | string;
};

function groupByVersion(rows: VersionComparisonRow[]): {
  chart: ChartPoint[];
  criteria: string[];
} {
  const byVersion = new Map<string, ChartPoint>();
  const criteriaSet = new Set<string>();
  for (const row of rows) {
    criteriaSet.add(row.criterion_name);
    const existing = byVersion.get(row.version) ?? { version: row.version };
    existing[row.criterion_name] = Number(row.avg_score.toFixed(4));
    byVersion.set(row.version, existing);
  }
  const chart = Array.from(byVersion.values()).sort((a, b) =>
    String(a.version).localeCompare(String(b.version)),
  );
  return { chart, criteria: Array.from(criteriaSet).sort() };
}

export function VersionComparisonChart({
  baseModelId,
}: {
  baseModelId: string;
}) {
  const { data, isLoading, error } = useVersionComparison(baseModelId);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">版本对比</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">加载版本数据中...</p>
        </CardContent>
      </Card>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">版本对比</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            该模型家族暂无多版本评测数据。创建新版本并运行同一任务后将在此显示分数变化。
          </p>
        </CardContent>
      </Card>
    );
  }

  const { chart, criteria } = groupByVersion(data);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">版本对比 (跨版本得分)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="version"
                tick={{ fontSize: 11 }}
                label={{
                  value: "版本",
                  position: "insideBottom",
                  offset: -2,
                  style: { fontSize: 11 },
                }}
              />
              <YAxis
                domain={[0, 1]}
                tick={{ fontSize: 11 }}
                label={{
                  value: "平均分",
                  angle: -90,
                  position: "insideLeft",
                  style: { fontSize: 11 },
                }}
              />
              <Tooltip
                contentStyle={{
                  fontSize: 11,
                  backgroundColor: "hsl(var(--background))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: 6,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {criteria.map((c, idx) => (
                <Line
                  key={c}
                  type="monotone"
                  dataKey={c}
                  stroke={LINE_COLORS[idx % LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
