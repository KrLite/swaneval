"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Play,
  Pause,
  Square,
  BarChart3,
  Database,
  Cpu,
  Settings,
  FileText,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

// Demo data
const mockTasks = [
  { id: 1, name: "Qwen2.5-7B on GSM8K", status: "running", progress: 65, dataset: "GSM8K", model: "Qwen/Qwen2.5-7B-Instruct" },
  { id: 2, name: "Llama-3.2 on MMLU", status: "completed", progress: 100, dataset: "MMLU", model: "meta-llama/Llama-3.2-3B-Instruct" },
  { id: 3, name: "Qwen2-1.5B on ARC", status: "pending", progress: 0, dataset: "ARC", model: "Qwen/Qwen2-1.5B-Instruct" },
  { id: 4, name: "Llama-3.2 on HumanEval", status: "failed", progress: 45, dataset: "HumanEval", model: "meta-llama/Llama-3.2-1B-Instruct" },
];

const mockModels = [
  { id: -1, name: "Qwen/Qwen2.5-0.5B-Instruct", type: "huggingface" },
  { id: -2, name: "Qwen/Qwen2.5-1.5B-Instruct", type: "huggingface" },
  { id: -3, name: "Qwen/Qwen2.5-7B-Instruct", type: "huggingface" },
];

const mockDatasets = [
  { id: -1, name: "MMLU", tags: ["knowledge", "reasoning"] },
  { id: -2, name: "C-Eval", tags: ["knowledge", "reasoning"] },
  { id: -3, name: "GSM8K", tags: ["math", "reasoning"] },
  { id: -4, name: "MATH", tags: ["math"] },
  { id: -7, name: "HumanEval", tags: ["code"] },
];

function getStatusIcon(status: string) {
  switch (status) {
    case "running":
      return <Play className="h-4 w-4 text-blue-500" />;
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case "failed":
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-gray-500" />;
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case "running":
      return "text-blue-500";
    case "completed":
      return "text-green-500";
    case "failed":
      return "text-red-500";
    default:
      return "text-gray-500";
  }
}

export default function EvaluationsPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">EvalScope GUI</h1>
          </div>
          <div className="flex items-center gap-4">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Evaluation
            </Button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 border-r bg-white min-h-[calc(100vh-64px)]">
          <nav className="p-4 space-y-2">
            <Link
              href="/evaluations"
              className="flex items-center gap-3 rounded-lg bg-primary/10 px-3 py-2 text-primary"
            >
              <BarChart3 className="h-5 w-5" />
              Evaluations
            </Link>
            <Link
              href="/models"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Cpu className="h-5 w-5" />
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
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <TrendingUp className="h-5 w-5" />
              Results
            </Link>
            <Link
              href="/settings"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Settings className="h-5 w-5" />
              Settings
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <Tabs defaultValue="tasks" className="space-y-6">
            <div className="flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="tasks">Tasks</TabsTrigger>
                <TabsTrigger value="models">Models</TabsTrigger>
                <TabsTrigger value="datasets">Datasets</TabsTrigger>
              </TabsList>
            </div>

            {/* Tasks Tab */}
            <TabsContent value="tasks" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockTasks.length}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Running</CardTitle>
                    <Play className="h-4 w-4 text-blue-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockTasks.filter(t => t.status === "running").length}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Completed</CardTitle>
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockTasks.filter(t => t.status === "completed").length}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Failed</CardTitle>
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {mockTasks.filter(t => t.status === "failed").length}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Evaluation Tasks</CardTitle>
                  <CardDescription>Manage and monitor your evaluation tasks</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockTasks.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-center justify-between rounded-lg border p-4"
                      >
                        <div className="flex items-center gap-4">
                          {getStatusIcon(task.status)}
                          <div>
                            <div className="font-medium">{task.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {task.model}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-sm text-muted-foreground">
                            {task.dataset}
                          </div>
                          <div className="w-32">
                            <Progress value={task.progress} className="h-2" />
                          </div>
                          <div className={`text-sm font-medium ${getStatusColor(task.status)}`}>
                            {task.progress}%
                          </div>
                          <div className="flex gap-2">
                            {task.status === "running" && (
                              <>
                                <Button variant="outline" size="icon">
                                  <Pause className="h-4 w-4" />
                                </Button>
                                <Button variant="outline" size="icon">
                                  <Square className="h-4 w-4" />
                                </Button>
                              </>
                            )}
                            <Button variant="outline" size="icon">
                              <FileText className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Models Tab */}
            <TabsContent value="models" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Available Models</CardTitle>
                  <CardDescription>Models available for evaluation</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {mockModels.map((model) => (
                      <div
                        key={model.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div className="flex items-center gap-3">
                          <Cpu className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{model.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {model.type}
                            </div>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          Select
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Datasets Tab */}
            <TabsContent value="datasets" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Available Datasets</CardTitle>
                  <CardDescription>Benchmarks and datasets for evaluation</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {mockDatasets.map((dataset) => (
                      <div
                        key={dataset.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div className="flex items-center gap-3">
                          <Database className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{dataset.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {dataset.tags.join(", ")}
                            </div>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          Select
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  );
}