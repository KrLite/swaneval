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
  Cpu,
  Globe,
  Server,
  Key,
  Trash2,
  Edit,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";

// Demo data
const mockModels = [
  { id: "1", name: "Qwen/Qwen2.5-0.5B-Instruct", type: "huggingface", status: "ready", provider: "HuggingFace" },
  { id: "2", name: "Qwen/Qwen2.5-1.5B-Instruct", type: "huggingface", status: "ready", provider: "HuggingFace" },
  { id: "3", name: "Qwen/Qwen2.5-7B-Instruct", type: "huggingface", status: "downloading", provider: "HuggingFace" },
  { id: "4", name: "meta-llama/Llama-3.2-1B-Instruct", type: "huggingface", status: "ready", provider: "HuggingFace" },
  { id: "5", name: "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", type: "huggingface", status: "ready", provider: "HuggingFace" },
  { id: "6", name: "gpt-4o", type: "api", status: "ready", provider: "OpenAI" },
  { id: "7", name: "claude-sonnet-4-20250514", type: "api", status: "ready", provider: "Anthropic" },
  { id: "8", name: "/models/llama-3.1-8b", type: "local", status: "ready", provider: "Local" },
];

const modelTypes = [
  { value: "huggingface", label: "HuggingFace", icon: Globe },
  { value: "api", label: "API Endpoint", icon: Server },
  { value: "local", label: "Local Model", icon: Cpu },
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
    case "huggingface":
      return <Globe className="h-5 w-5" />;
    case "api":
      return <Server className="h-5 w-5" />;
    case "local":
      return <Cpu className="h-5 w-5" />;
    default:
      return <Cpu className="h-5 w-5" />;
  }
}

export default function ModelsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newModel, setNewModel] = useState({
    name: "",
    type: "huggingface",
    apiKey: "",
    apiEndpoint: "",
    localPath: "",
  });

  const filteredModels = mockModels.filter((model) => {
    const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === "all" || model.type === typeFilter;
    return matchesSearch && matchesType;
  });

  const handleAddModel = () => {
    // TODO: Connect to backend API
    console.log("Add model:", newModel);
    setIsAddDialogOpen(false);
    setNewModel({ name: "", type: "huggingface", apiKey: "", apiEndpoint: "", localPath: "" });
  };

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
              <Cpu className="h-5 w-5" />
              Evaluations
            </Link>
            <Link
              href="/models"
              className="flex items-center gap-3 rounded-lg bg-primary/10 px-3 py-2 text-primary"
            >
              <Cpu className="h-5 w-5" />
              Models
            </Link>
            <Link
              href="/datasets"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Cpu className="h-5 w-5" />
              Datasets
            </Link>
            <Link
              href="/results"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Cpu className="h-5 w-5" />
              Results
            </Link>
            <Link
              href="/settings"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted"
            >
              <Cpu className="h-5 w-5" />
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
                <h2 className="text-2xl font-bold">Model Management</h2>
                <p className="text-muted-foreground">Manage your evaluation models</p>
              </div>
              <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Model
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[600px]">
                  <DialogHeader>
                    <DialogTitle>Add New Model</DialogTitle>
                    <DialogDescription>
                      Configure a model for evaluation. Supports HuggingFace, API endpoints, and local models.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label>Model Type</Label>
                      <Select
                        value={newModel.type}
                        onValueChange={(value) => setNewModel({ ...newModel, type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select model type" />
                        </SelectTrigger>
                        <SelectContent>
                          {modelTypes.map((type) => (
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

                    {newModel.type === "huggingface" && (
                      <div className="grid gap-2">
                        <Label>Model Name or Path</Label>
                        <Input
                          placeholder="e.g., Qwen/Qwen2.5-7B-Instruct"
                          value={newModel.name}
                          onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
                        />
                        <p className="text-sm text-muted-foreground">
                          Enter the HuggingFace model ID (e.g., meta-llama/Llama-3.2-1B-Instruct)
                        </p>
                      </div>
                    )}

                    {newModel.type === "api" && (
                      <>
                        <div className="grid gap-2">
                          <Label>Model Name</Label>
                          <Input
                            placeholder="e.g., gpt-4o"
                            value={newModel.name}
                            onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label>API Endpoint</Label>
                          <Input
                            placeholder="e.g., https://api.openai.com/v1/chat/completions"
                            value={newModel.apiEndpoint}
                            onChange={(e) => setNewModel({ ...newModel, apiEndpoint: e.target.value })}
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label>API Key</Label>
                          <Input
                            type="password"
                            placeholder="sk-..."
                            value={newModel.apiKey}
                            onChange={(e) => setNewModel({ ...newModel, apiKey: e.target.value })}
                          />
                        </div>
                      </>
                    )}

                    {newModel.type === "local" && (
                      <div className="grid gap-2">
                        <Label>Local Model Path</Label>
                        <Input
                          placeholder="e.g., /models/llama-3.1-8b"
                          value={newModel.localPath}
                          onChange={(e) => setNewModel({ ...newModel, localPath: e.target.value })}
                        />
                      </div>
                    )}
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddModel}>Add Model</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {/* Filters */}
            <div className="flex gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search models..."
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
                  <SelectItem value="huggingface">HuggingFace</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="local">Local</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Models Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredModels.map((model) => (
                <Card key={model.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                          {getTypeIcon(model.type)}
                        </div>
                        <div>
                          <CardTitle className="text-sm">{model.name}</CardTitle>
                          <CardDescription className="text-xs">{model.provider}</CardDescription>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(model.status)}
                        <span className="text-sm capitalize text-muted-foreground">{model.status}</span>
                      </div>
                      <div className="flex gap-2">
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

            {filteredModels.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Cpu className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold">No models found</h3>
                <p className="text-muted-foreground">Try adjusting your search or filter criteria</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}