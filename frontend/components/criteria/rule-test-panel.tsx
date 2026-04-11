"use client";

import { useMemo } from "react";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

interface RuleTestPanelProps {
  pattern: string;
  matchMode: string;
  keywords: string;
  keywordsMode: string;
  sample: string;
  onSampleChange: (v: string) => void;
}

interface TestResult {
  label: string;
  ok: boolean;
  detail: string;
}

function runRuleTests(props: RuleTestPanelProps): TestResult[] {
  const { pattern, matchMode, keywords, keywordsMode, sample } = props;
  if (!sample.trim()) return [];

  const results: TestResult[] = [];

  if (pattern) {
    try {
      const rx = new RegExp(pattern);
      const match = rx.exec(sample);
      if (matchMode === "exact") {
        const wholeMatch = sample === (match?.[0] ?? "");
        results.push({
          label: `正则 (${matchMode})`,
          ok: wholeMatch,
          detail: wholeMatch ? "整体匹配成功" : "整体不匹配",
        });
      } else if (matchMode === "extract") {
        const group = match?.[1] ?? match?.[0] ?? "";
        results.push({
          label: `正则 (${matchMode})`,
          ok: !!group,
          detail: group ? `提取: ${group}` : "未捕获",
        });
      } else {
        results.push({
          label: `正则 (${matchMode})`,
          ok: !!match,
          detail: match ? `匹配: ${match[0]}` : "无匹配",
        });
      }
    } catch (e) {
      results.push({
        label: "正则",
        ok: false,
        detail: `语法错误: ${e instanceof Error ? e.message : "unknown"}`,
      });
    }
  }

  const kwList = keywords
    .split(/[\n,]/)
    .map((k) => k.trim())
    .filter(Boolean);
  if (kwList.length > 0) {
    const hits = kwList.filter((k) => sample.includes(k));
    const ok = keywordsMode === "all" ? hits.length === kwList.length : hits.length > 0;
    results.push({
      label: `关键词 (${keywordsMode === "all" ? "全部" : "任一"})`,
      ok,
      detail:
        hits.length === 0
          ? "无命中"
          : `命中 ${hits.length}/${kwList.length}: ${hits.slice(0, 3).join(", ")}`,
    });
  }

  return results;
}

export function RuleTestPanel(props: RuleTestPanelProps) {
  const results = useMemo(() => runRuleTests(props), [props]);
  const allPass = results.length > 0 && results.every((r) => r.ok);

  return (
    <div className="rounded-md border bg-muted/30 p-2.5 space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-medium">规则预览</Label>
        {results.length > 0 && (
          <Badge
            variant={allPass ? "success" : "outline"}
            className="text-[10px]"
          >
            {allPass ? "全部通过" : "有未通过项"}
          </Badge>
        )}
      </div>
      <textarea
        value={props.sample}
        onChange={(e) => props.onSampleChange(e.target.value)}
        placeholder="粘贴一段模型输出样本以实时预览规则命中情况..."
        rows={3}
        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
      />
      {results.length > 0 && (
        <div className="space-y-1">
          {results.map((r, i) => (
            <div
              key={i}
              className="flex items-center justify-between text-[11px]"
            >
              <span className="text-muted-foreground">{r.label}</span>
              <span
                className={`font-mono ${r.ok ? "text-emerald-600 dark:text-emerald-400" : "text-destructive"}`}
              >
                {r.ok ? "✓" : "✗"} {r.detail}
              </span>
            </div>
          ))}
        </div>
      )}
      {results.length === 0 && props.sample.trim() && (
        <p className="text-[11px] text-muted-foreground">
          请填写正则表达式或关键词以查看匹配结果。
        </p>
      )}
    </div>
  );
}
