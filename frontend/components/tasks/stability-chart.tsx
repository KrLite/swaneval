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
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useStabilityStats } from "@/lib/hooks/use-tasks";
import type { StabilityStats } from "@/lib/types";

const LINE_COLORS = [
  "#7C3AED",
  "#2563EB",
  "#059669",
  "#DC2626",
  "#D97706",
  "#DB2777",
];

type ChartPoint = {
  run_index: number;
  [criterion: string]: number;
};

function toChartPoints(stats: StabilityStats[]): ChartPoint[] {
  const runCount = Math.max(0, ...stats.map((s) => s.per_run_scores.length));
  const points: ChartPoint[] = [];
  for (let i = 0; i < runCount; i++) {
    const point: ChartPoint = { run_index: i + 1 };
    for (const s of stats) {
      if (i < s.per_run_scores.length) {
        point[s.criterion_name] = Number(s.per_run_scores[i].toFixed(4));
      }
    }
    points.push(point);
  }
  return points;
}

export function StabilityChart({ taskId }: { taskId: string }) {
  const { data, isLoading, error } = useStabilityStats(taskId);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">稳定性分析</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">加载稳定性统计中...</p>
        </CardContent>
      </Card>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">稳定性分析</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            该任务未启用扰动测试（repeat_count &le; 1），无稳定性统计可用。
          </p>
        </CardContent>
      </Card>
    );
  }

  const chartPoints = toChartPoints(data);
  const runCount = data[0]?.run_count ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          <span>稳定性分析</span>
          <Badge variant="secondary" className="text-[10px]">
            {runCount} 次重复运行
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartPoints}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="run_index"
                label={{
                  value: "运行次数",
                  position: "insideBottom",
                  offset: -2,
                  style: { fontSize: 11 },
                }}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                domain={[0, 1]}
                tick={{ fontSize: 11 }}
                label={{
                  value: "分数",
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
              {data.map((s, idx) => (
                <Line
                  key={s.criterion_id}
                  type="monotone"
                  dataKey={s.criterion_name}
                  stroke={LINE_COLORS[idx % LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-2">
          {data.map((s) => (
            <div
              key={s.criterion_id}
              className="rounded-md border p-2.5 text-xs"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">{s.criterion_name}</span>
                <span className="font-mono text-muted-foreground">
                  {(s.mean_score * 100).toFixed(1)}% ± {(s.std_dev * 100).toFixed(2)}%
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-[11px] text-muted-foreground">
                <div>
                  <dt>均值</dt>
                  <dd className="font-mono text-foreground">
                    {s.mean_score.toFixed(4)}
                  </dd>
                </div>
                <div>
                  <dt>标准差</dt>
                  <dd className="font-mono text-foreground">
                    {s.std_dev.toFixed(4)}
                  </dd>
                </div>
                <div>
                  <dt>95% CI 下界</dt>
                  <dd className="font-mono text-foreground">
                    {s.ci_95_lower.toFixed(4)}
                  </dd>
                </div>
                <div>
                  <dt>95% CI 上界</dt>
                  <dd className="font-mono text-foreground">
                    {s.ci_95_upper.toFixed(4)}
                  </dd>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
