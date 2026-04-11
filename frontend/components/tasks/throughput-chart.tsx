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
import { useThroughput } from "@/lib/hooks/use-results";
import type { ThroughputPoint } from "@/lib/types";

const LINE_COLORS = [
  "#7C3AED",
  "#2563EB",
  "#059669",
  "#DC2626",
  "#D97706",
  "#DB2777",
];

type ChartPoint = {
  concurrency: number;
  [model: string]: number;
};

function groupByModel(points: ThroughputPoint[]): {
  chart: ChartPoint[];
  models: string[];
} {
  const byConcurrency = new Map<number, ChartPoint>();
  const modelSet = new Set<string>();
  for (const p of points) {
    modelSet.add(p.model_name);
    const existing = byConcurrency.get(p.concurrency) ?? {
      concurrency: p.concurrency,
    };
    existing[p.model_name] = p.avg_tokens_per_sec;
    byConcurrency.set(p.concurrency, existing);
  }
  const chart = Array.from(byConcurrency.values()).sort(
    (a, b) => a.concurrency - b.concurrency,
  );
  return { chart, models: Array.from(modelSet).sort() };
}

export function ThroughputChart({ taskIds }: { taskIds: string[] }) {
  const { data, isLoading, error } = useThroughput(taskIds);

  if (taskIds.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">吞吐量对比</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            选择至少一个任务以查看 token 生成速度随并发度的变化。
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">吞吐量对比</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">加载吞吐数据中...</p>
        </CardContent>
      </Card>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">吞吐量对比</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            所选任务暂无吞吐数据。请确认任务已完成且有有效结果。
          </p>
        </CardContent>
      </Card>
    );
  }

  const { chart, models } = groupByModel(data);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">吞吐量对比（并发 × token/s）</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="concurrency"
                tick={{ fontSize: 11 }}
                label={{
                  value: "并发度",
                  position: "insideBottom",
                  offset: -2,
                  style: { fontSize: 11 },
                }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                label={{
                  value: "tokens/s",
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
              {models.map((m, idx) => (
                <Line
                  key={m}
                  type="monotone"
                  dataKey={m}
                  stroke={LINE_COLORS[idx % LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-1 text-[11px] text-muted-foreground">
          {data.map((p) => (
            <div key={p.task_id} className="flex justify-between gap-2">
              <span className="truncate">
                {p.model_name} · 并发 {p.concurrency} · {p.task_name}
              </span>
              <span className="font-mono whitespace-nowrap">
                {p.avg_tokens_per_sec.toFixed(1)} tok/s · TTFT{" "}
                {p.avg_first_token_ms.toFixed(0)} ms
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
