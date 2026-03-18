"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Search,
  Database,
  Globe,
  Upload,
  Server,
  Trash2,
  Edit,
  Eye,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileJson,
  FileText,
  FolderOpen,
} from "lucide-react";

// Demo data
const mockDatasets = [
  { id: "1", name: "mmlu", type: "preset", provider: "EvalScope", version: "1.0", samples: 15000, status: "ready" },
  { id: "2", name: "c-eval", type: "preset", provider: "EvalScope", version: "1.2", samples: 12000, status: "ready" },
  { id: "3", name: "gsm8k", type: "preset", provider: "EvalScope", version: "1.0", samples: 8500, status: "ready" },
  { id: "4", name: "math", type: "huggingface", provider: "HuggingFace", version: "1.0", samples: 12500, status: "ready" },
  { id: "5", name: "custom_dataset_v1", type: "custom", provider: "Local Upload", version: "1.0", samples: 2500, status: "ready" },
  { id: "6", name: "arc", type: "huggingface", provider: "HuggingFace", version: "1.0", samples: 30000, status: "downloading" },
];

const datasetTypes = [
  { value: "preset", label: "Preset Dataset", icon: Database },
  { value: "huggingface", label: "HuggingFace", icon: Globe },
  { value: "custom", label: "Custom Upload", icon: Upload },
];

function getStatusIcon(status: string) {
  switch (status) {
    case "ready":
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case "downloading":
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    case "error":
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Loader2 className="h-4 w-4 text-gray-500 animate-spin" />;
  }
}

function getTypeIcon(type: string) {
  switch (type) {
    case "preset":
      return <Database className="h-5 w-5" />;
    case "huggingface":
      return <Globe className="h-5 w-5" />;
    case "custom":
      return <Upload className="h-5 w-5" />;
    default:
      return <Database className="h-5 w-5" />;
  }
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num);
}

export default function DatasetsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [previewDataset, setPreviewDataset] = useState<any>(null);
  const [newDataset, setNewDataset] = useState({
    name: "",
    type: "preset",
    huggingfacePath: "",
    version: "1.0",
  });

  const filteredDatasets = mockDatasets.filter((dataset) => {
    const matchesSearch = dataset.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === "all" || dataset.type === typeFilter;
    return matchesSearch && matchesType;
  });

  const handleAddDataset = () => {
    // TODO: Connect to backend API
    console.log("Add dataset:", newDataset);
    setIsAddDialogOpen(false);
    setNewDataset({ name: "", type: "preset", huggingfacePath: "", version: "1.0" });
  };

  const handlePreview = (dataset: any) => {
    setPreviewDataset(dataset);
    setIsPreviewDialogOpen(true);
  };

  const presetDatasets = [
    { id: "mmlu", name: "MMLU", description: "Massive Multitask Language Understanding" },
    { id: "c-eval", name: "C-Eval", description: "Chinese evaluation suite" },
    { id: "gsm8k", name: "GSM8K", description: "Grade School Math" },
    { id: "humaneval", name: "HumanEval", description: "Code generation benchmark" },
    { id: "mbpp", name: "MBPP", description: "Python programming benchmark" },
    { id: "bbh", name: "BBH", description: "Big Bench Hard" },
    { id: "truthfulqa", name: "TruthfulQA", description: "Truthfulness evaluation" },
    { id: "ifeval", name: "IFEval", description: "Instruction following evaluation" },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">EvalScope GUI</h1>
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
              className="flex items-center gap-3 rounded-lg bg-primary/10 px-3 py-2 text-primary"
            >
              <Database className="h-5 w-5" />
              Datasets
            </Link>
            <Link
              href="/results"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
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
                <h2 className="text-2xl font-bold">Dataset Management</h2>
                <p className="text-muted-foreground">Manage evaluation datasets</p>
              </div>
              <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Dataset
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[600px]">
                  <DialogHeader>
                    <DialogTitle>Add New Dataset</DialogTitle>
                    <DialogDescription>
                      Import a dataset from preset collections, HuggingFace, or upload custom data.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label>Dataset Source</Label>
                      <Select
                        value={newDataset.type}
                        onValueChange={(value) => setNewDataset({ ...newDataset, type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select dataset source" />
                        </SelectTrigger>
                        <SelectContent>
                          {datasetTypes.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex items-center gap-2">
                                <type.icon className="h-4 w-4" />
                                {type.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {newDataset.type === "preset" && (
                      <div className="grid gap-2">
                        <Label>Select Preset Dataset</Label>
                        <Select
                          value={newDataset.name}
                          onValueChange={(value) => setNewDataset({ ...newDataset, name: value })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Choose a preset dataset" />
                          </SelectTrigger>
                          <SelectContent>
                            {presetDatasets.map((preset) => (
                              <SelectItem key={preset.id} value={preset.id}>
                                <div>
                                  <div className="font-medium">{preset.name}</div>
                                  <div className="text-xs text-muted-foreground">{preset.description}</div>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {newDataset.type === "huggingface" && (
                      <>
                        <div className="grid gap-2">
                          <Label>HuggingFace Dataset Path</Label>
                          <Input
                            placeholder="e.g., openai/gsm8k"
                            value={newDataset.huggingfacePath}
                            onChange={(e) => setNewDataset({ ...newDataset, huggingfacePath: e.target.value })}
                          />
                          <p className="text-sm text-muted-foreground">
                            Enter the HuggingFace dataset path (e.g., openai/gsm8k)
                          </p>
                        </div>
                        <div className="grid gap-2">
                          <Label>Dataset Name (Alias)</Label>
                          <Input
                            placeholder="e.g., my_custom_dataset"
                            value={newDataset.name}
                            onChange={(e) => setNewDataset({ ...newDataset, name: e.target.value })}
                          />
                        </div>
                      </>
                    )}

                    {newDataset.type === "custom" && (
                      <>
                        <div className="grid gap-2">
                          <Label>Dataset Name</Label>
                          <Input
                            placeholder="e.g., my_evaluation_data"
                            value={newDataset.name}
                            onChange={(e) => setNewDataset({ ...newDataset, name: e.target.value })}
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label>Upload File</Label>
                          <div className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:bg-muted/50 transition-colors">
                            <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                            <p className="text-sm text-muted-foreground">
                              Click to upload or drag and drop
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              JSONL, CSV, Parquet, or Excel (max 100MB)
                            </p>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddDataset}>Import Dataset</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {/* Filters */}
            <div className="flex gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search datasets..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="preset">Preset</SelectItem>
                  <SelectItem value="huggingface">HuggingFace</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Datasets Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredDatasets.map((dataset) => (
                <Card key={dataset.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                          {getTypeIcon(dataset.type)}
                        </div>
                        <div>
                          <CardTitle className="text-sm">{dataset.name}</CardTitle>
                          <CardDescription className="text-xs">{dataset.provider}</CardDescription>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Samples</span>
                        <span className="font-medium">{formatNumber(dataset.samples)}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Version</span>
                        <span className="font-medium">{dataset.version}</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(dataset.status)}
                        <span className="text-sm capitalize text-muted-foreground">{dataset.status}</span>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => handlePreview(dataset)}>
                          <Eye className="h-3 w-3" />
                        </Button>
                        <Button variant="outline" size="icon" className="h-8 w-8">
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button variant="outline" size="icon" className="h-8 w-8">
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredDatasets.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Database className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold">No datasets found</h3>
                <p className="text-muted-foreground">Try adjusting your search or filter criteria</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Preview Dialog */}
      <Dialog open={isPreviewDialogOpen} onOpenChange={setIsPreviewDialogOpen}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle>Dataset Preview: {previewDataset?.name}</DialogTitle>
            <DialogDescription>
              {previewDataset?.samples} samples | {previewDataset?.type} | {previewDataset?.provider}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-md border">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">ID</th>
                      <th className="px-4 py-2 text-left font-medium">Question</th>
                      <th className="px-4 py-2 text-left font-medium">Answer</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="px-4 py-2">1</td>
                      <td className="px-4 py-2">What is 2 + 2?</td>
                      <td className="px-4 py-2 text-green-600">4</td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-4 py-2">2</td>
                      <td className="px-4 py-2">What is the capital of France?</td>
                      <td className="px-4 py-2 text-green-600">Paris</td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-4 py-2">3</td>
                      <td className="px-4 py-2">What is the square root of 16?</td>
                      <td className="px-4 py-2 text-green-600">4</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center">
              Showing first 3 of {previewDataset?.samples} samples
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPreviewDialogOpen(false)}>
              Close
            </Button>
            <Button onClick={() => console.log("Use dataset:", previewDataset)}>
              Use Dataset
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}