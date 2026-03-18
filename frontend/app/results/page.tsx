"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import {
  Database,
  Download,
  FileText,
  BarChart3,
  Radar as RadarIcon,
  TrendingUp,
  Trophy,
  Filter,
} from "lucide-react";

// Mock data for charts
const comparisonData = [
  { model: "Qwen2.5-0.5B", accuracy: 45.2, precision: 48.1, recall: 44.8, f1: 46.4 },
  { model: "Qwen2.5-1.5B", accuracy: 62.8, precision: 64.5, recall: 61.9, f1: 63.2 },
  { model: "Llama-3.2-1B", accuracy: 58.4, precision: 59.7, recall: 57.2, f1: 58.4 },
  { model: "DeepSeek-R1-1.5B", accuracy: 71.5, precision: 73.2, recall: 70.1, f1: 71.6 },
  { model: "GPT-4o", accuracy: 89.2, precision: 90.1, recall: 88.5, f1: 89.3 },
];

const radarData = [
  { metric: "Accuracy", value: 85, fullMark: 100 },
  { metric: "Precision", value: 88, fullMark: 100 },
  { metric: "Recall", value: 82, fullMark: 100 },
  { metric: "F1 Score", value: 85, fullMark: 100 },
  { metric: "Latency", value: 75, fullMark: 100 },
  { metric: "Cost", value: 60, fullMark: 100 },
];

const tokenSpeedData = [
  { model: "Qwen2.5-0.5B", ttft: 120, tpot: 45, throughput: 850 },
  { model: "Qwen2.5-1.5B", ttft: 280, tpot: 85, throughput: 420 },
  { model: "Llama-3.2-1B", ttft: 250, tpot: 78, throughput: 480 },
  { model: "DeepSeek-R1-1.5B", ttft: 310, tpot: 92, throughput: 380 },
  { model: "GPT-4o", ttft: 450, tpot: 120, throughput: 180 },
];

const versionTrendData = [
  { version: "v1.0", accuracy: 72.5, precision: 74.2, recall: 71.8 },
  { version: "v1.1", accuracy: 74.8, precision: 76.1, recall: 73.9 },
  { version: "v1.2", accuracy: 78.2, precision: 79.5, recall: 77.1 },
  { version: "v1.3", accuracy: 82.4, precision: 83.8, recall: 81.2 },
  { version: "v1.4", accuracy: 85.6, precision: 86.9, recall: 84.5 },
];

const leaderboardData = [
  { rank: 1, model: "GPT-4o", score: 89.3, trend: "up" },
  { rank: 2, model: "Claude-Sonnet-4", score: 87.8, trend: "up" },
  { rank: 3, model: "DeepSeek-R1-1.5B", score: 71.6, trend: "up" },
  { rank: 4, model: "Qwen2.5-1.5B", score: 63.2, trend: "stable" },
  { rank: 5, model: "Llama-3.2-1B", score: 58.4, trend: "down" },
  { rank: 6, model: "Qwen2.5-0.5B", score: 46.4, trend: "stable" },
];

export default function ResultsPage() {
  const [metricFilter, setMetricFilter] = useState("accuracy");
  const [timeRange, setTimeRange] = useState("all");

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case "down":
        return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />;
      default:
        return <span className="text-muted-foreground">-</span>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">EvalScope GUI</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">Last Week</SelectItem>
                <SelectItem value="month">Last Month</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 border-r bg-white min-h-[calc(100vh-64px)]">
          <nav className="p-4 space-y-2">
            <Link
              href="/evaluations"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Database className="h-5 w-5" />
              Evaluations
            </Link>
            <Link
              href="/models"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Database className="h-5 w-5" />
              Models
            </Link>
            <Link
              href="/datasets"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Database className="h-5 w-5" />
              Datasets
            </Link>
            <Link
              href="/results"
              className="flex items-center gap-3 rounded-lg bg-primary/10 px-3 py-2 text-primary"
            >
              <Database className="h-5 w-5" />
              Results
            </Link>
            <Link
              href="/settings"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Database className="h-5 w-5" />
              Settings
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Results & Analytics</h2>
                <p className="text-muted-foreground">View evaluation results and performance metrics</p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  Filter
                </Button>
                <Button variant="outline" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Report
                </Button>
              </div>
            </div>

            {/* Tabs for different views */}
            <Tabs defaultValue="comparison" className="space-y-4">
              <TabsList>
                <TabsTrigger value="comparison" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Comparison
                </TabsTrigger>
                <TabsTrigger value="radar" className="flex items-center gap-2">
                  <RadarIcon className="h-4 w-4" />
                  Capability
                </TabsTrigger>
                <TabsTrigger value="performance" className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Performance
                </TabsTrigger>
                <TabsTrigger value="leaderboard" className="flex items-center gap-2">
                  <Trophy className="h-4 w-4" />
                  Leaderboard
                </TabsTrigger>
              </TabsList>

              {/* Comparison Charts */}
              <TabsContent value="comparison" className="space-y-4">
                <div className="grid gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Model Comparison</CardTitle>
                      <CardDescription>Compare models across different metrics</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={comparisonData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="model" tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="accuracy" fill="#3b82f6" name="Accuracy" />
                            <Bar dataKey="precision" fill="#10b981" name="Precision" />
                            <Bar dataKey="recall" fill="#f59e0b" name="Recall" />
                            <Bar dataKey="f1" fill="#8b5cf6" name="F1 Score" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Data Table */}
                <Card>
                  <CardHeader>
                    <CardTitle>Detailed Results</CardTitle>
                    <CardDescription>Raw metrics for all evaluated models</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="border-b bg-muted">
                          <tr>
                            <th className="px-4 py-3 text-left font-medium">Model</th>
                            <th className="px-4 py-3 text-right font-medium">Accuracy</th>
                            <th className="px-4 py-3 text-right font-medium">Precision</th>
                            <th className="px-4 py-3 text-right font-medium">Recall</th>
                            <th className="px-4 py-3 text-right font-medium">F1 Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {comparisonData.map((row, idx) => (
                            <tr key={idx} className="border-b hover:bg-muted/50">
                              <td className="px-4 py-3 font-medium">{row.model}</td>
                              <td className="px-4 py-3 text-right">{row.accuracy}%</td>
                              <td className="px-4 py-3 text-right">{row.precision}%</td>
                              <td className="px-4 py-3 text-right">{row.recall}%</td>
                              <td className="px-4 py-3 text-right">{row.f1}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Radar Charts */}
              <TabsContent value="radar" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>GPT-4o Capability Overview</CardTitle>
                      <CardDescription>Multi-dimensional performance analysis</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart data={radarData}>
                            <PolarGrid />
                            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                            <Radar name="Score" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>DeepSeek-R1-1.5B</CardTitle>
                      <CardDescription>Multi-dimensional performance analysis</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart data={radarData.map(d => ({ ...d, value: d.value * 0.8 }))}>
                            <PolarGrid />
                            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                            <Radar name="Score" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Performance Charts */}
              <TabsContent value="performance" className="space-y-4">
                <div className="grid gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Token Speed Comparison</CardTitle>
                      <CardDescription>Time to First Token (TTFT), Time Per Output Token (TPOT)</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={tokenSpeedData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" tick={{ fontSize: 12 }} />
                            <YAxis dataKey="model" type="category" width={150} tick={{ fontSize: 11 }} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="ttft" fill="#3b82f6" name="TTFT (ms)" />
                            <Bar dataKey="tpot" fill="#10b981" name="TPOT (ms)" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Cross-Version Performance Trend</CardTitle>
                      <CardDescription>Model performance improvements over versions</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={versionTrendData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="version" tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} domain={[60, 100]} />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} name="Accuracy" />
                            <Line type="monotone" dataKey="precision" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} name="Precision" />
                            <Line type="monotone" dataKey="recall" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} name="Recall" />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Throughput Over Time</CardTitle>
                      <CardDescription>Tokens per second by model</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={tokenSpeedData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="model" tick={{ fontSize: 11 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip />
                            <Area type="monotone" dataKey="throughput" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} name="Tokens/sec" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Leaderboard */}
              <TabsContent value="leaderboard" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Model Leaderboard</CardTitle>
                    <CardDescription>Rankings based on overall score</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {leaderboardData.map((entry) => (
                        <div
                          key={entry.rank}
                          className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            <div
                              className={`flex h-8 w-8 items-center justify-center rounded-full font-bold ${
                                entry.rank === 1
                                  ? "bg-yellow-500 text-white"
                                  : entry.rank === 2
                                  ? "bg-gray-400 text-white"
                                  : entry.rank === 3
                                  ? "bg-orange-400 text-white"
                                  : "bg-muted text-muted-foreground"
                              }`}
                            >
                              {entry.rank}
                            </div>
                            <div>
                              <div className="font-medium">{entry.model}</div>
                              <div className="text-sm text-muted-foreground">Overall Score</div>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-2xl font-bold">{entry.score}</span>
                            {getTrendIcon(entry.trend)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
}