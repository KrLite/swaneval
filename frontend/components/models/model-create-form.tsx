"use client";

import { useState } from "react";
import { JsonImportBar } from "@/components/json-import-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PanelField } from "@/components/panel-helpers";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Loader2, Check, X as XIcon, Globe, Server, Search, ExternalLink } from "lucide-react";
import { useCreateModel, useDeployModel, usePreflightHub, type HubPreflightResult } from "@/lib/hooks/use-models";
import { useAuthStore } from "@/lib/stores/auth";
import { useUserTokens } from "@/lib/hooks/use-users";
import { useClusters } from "@/lib/hooks/use-clusters";

interface ModelCreateFormProps {
  onSuccess: () => void;
  onClose: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function ModelCreateForm({ onSuccess, onClose: _onClose }: ModelCreateFormProps) {
  const create = useCreateModel();
  const deploy = useDeployModel();
  const preflight = usePreflightHub();
  const [preflightResult, setPreflightResult] = useState<HubPreflightResult | null>(null);
  const user = useAuthStore((s) => s.user);
  const { data: tokenStatus } = useUserTokens();
  const { data: clusters = [] } = useClusters();
  const accountHref = user?.role === "admin" ? `/admin?user=${user.id}` : "/account";

  const [mode, setMode] = useState<"api" | "selfhosted">("api");
  const [deployError, setDeployError] = useState("");
  const [deployPhase, setDeployPhase] = useState<"" | "creating" | "deploying" | "done">("");

  // API model form
  const [apiForm, setApiForm] = useState({
    name: "", provider: "", endpoint_url: "", api_key: "",
    api_format: "openai", model_name: "", max_tokens: "4096", description: "",
  });

  // Self-hosted model form (includes deployment config)
  const [shForm, setShForm] = useState({
    name: "", source: "huggingface" as "huggingface" | "modelscope",
    model_id: "", description: "", max_tokens: "4096",
    cluster_id: "", gpu_count: "1", memory_gb: "40",
  });

  const importFromJson = (text: string) => {
    const data = JSON.parse(text);
    if (data.model_type === "huggingface" || data.model_type === "modelscope") {
      setMode("selfhosted");
      setShForm((f) => ({
        ...f,
        name: data.name ?? f.name,
        source: data.model_type ?? f.source,
        model_id: data.model_name ?? data.source_model_id ?? f.model_id,
        description: data.description ?? f.description,
        max_tokens: data.max_tokens != null ? String(data.max_tokens) : f.max_tokens,
      }));
    } else {
      setMode("api");
      setApiForm((f) => ({
        ...f,
        name: data.name ?? f.name,
        provider: data.provider ?? f.provider,
        endpoint_url: data.endpoint_url ?? f.endpoint_url,
        api_key: data.api_key ?? f.api_key,
        api_format: data.api_format ?? f.api_format,
        model_name: data.model_name ?? f.model_name,
        max_tokens: data.max_tokens != null ? String(data.max_tokens) : f.max_tokens,
        description: data.description ?? f.description,
      }));
    }
  };

  const handleCreateApi = async (e: React.FormEvent) => {
    e.preventDefault();
    await create.mutateAsync({
      name: apiForm.name,
      provider: apiForm.provider,
      endpoint_url: apiForm.endpoint_url,
      api_key: apiForm.api_key || undefined,
      model_type: "api",
      api_format: apiForm.api_format as "openai" | "anthropic",
      model_name: apiForm.model_name || undefined,
      max_tokens: apiForm.max_tokens ? parseInt(apiForm.max_tokens) : undefined,
      description: apiForm.description || undefined,
    });
    onSuccess();
  };

  const handleCreateAndDeploy = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeployError("");
    const isHF = shForm.source === "huggingface";
    const displayName = shForm.name || shForm.model_id.split("/").pop() || "";

    // Step 1: Create the model record
    setDeployPhase("creating");
    let modelId: string;
    try {
      const created = await create.mutateAsync({
        name: displayName,
        provider: shForm.source,
        endpoint_url: isHF
          ? `https://api-inference.huggingface.co/models/${shForm.model_id}/v1/chat/completions`
          : `https://api-inference.modelscope.cn/v1/chat/completions`,
        model_type: shForm.source,
        api_format: "openai",
        model_name: shForm.model_id,
        source_model_id: shForm.model_id,
        max_tokens: shForm.max_tokens ? parseInt(shForm.max_tokens) : undefined,
        description: shForm.description || undefined,
      });
      modelId = created.id;
    } catch (err: unknown) {
      setDeployPhase("");
      setDeployError(err instanceof Error ? err.message : "注册模型失败");
      return;
    }

    // Step 2: Deploy to cluster (if cluster selected) — non-blocking
    if (shForm.cluster_id) {
      setDeployPhase("deploying");
      try {
        await deploy.mutateAsync({
          model_id: modelId,
          cluster_id: shForm.cluster_id,
          gpu_count: parseInt(shForm.gpu_count) || 1,
          memory_gb: parseInt(shForm.memory_gb) || 40,
        });
        // Deploy is background — returns immediately, model shows "deploying" in table
      } catch (err: unknown) {
        setDeployPhase("");
        setDeployError(err instanceof Error ? err.message : "部署请求失败（模型已注册）");
        setTimeout(() => onSuccess(), 2000);
        return;
      }
    }

    setDeployPhase("done");
    onSuccess();
  };

  const tokenSet = shForm.source === "huggingface" ? tokenStatus?.hf_token_set : tokenStatus?.ms_token_set;
  const tokenLabel = shForm.source === "huggingface" ? "HF Token" : "MS Token";
  const isSubmitting = create.isPending || deploy.isPending || !!deployPhase;

  return (
    <>
      <JsonImportBar onImport={importFromJson} className="mb-3" />

      <Tabs value={mode} onValueChange={(v) => setMode(v as "api" | "selfhosted")}>
        <TabsList className="w-full mb-3">
          <TabsTrigger value="api" className="flex-1">
            <Globe className="mr-1.5 h-3.5 w-3.5" />
            API 模型
          </TabsTrigger>
          <TabsTrigger value="selfhosted" className="flex-1">
            <Server className="mr-1.5 h-3.5 w-3.5" />
            自托管模型
          </TabsTrigger>
        </TabsList>

        {/* ── API Model ── */}
        <TabsContent value="api">
          <form onSubmit={handleCreateApi} className="space-y-3">
            <PanelField label="显示名称" required>
              <Input
                value={apiForm.name}
                onChange={(e) => setApiForm({ ...apiForm, name: e.target.value })}
                placeholder="GPT-4o"
                required
              />
            </PanelField>
            <div className="grid grid-cols-2 gap-2">
              <PanelField label="提供商" required>
                <Input
                  value={apiForm.provider}
                  onChange={(e) => setApiForm({ ...apiForm, provider: e.target.value })}
                  placeholder="openai"
                  required
                />
              </PanelField>
              <PanelField label="API 协议">
                <Select
                  value={apiForm.api_format}
                  onValueChange={(v) => setApiForm({ ...apiForm, api_format: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                  </SelectContent>
                </Select>
              </PanelField>
            </div>
            <PanelField label="端点 URL" required>
              <Input
                value={apiForm.endpoint_url}
                onChange={(e) => setApiForm({ ...apiForm, endpoint_url: e.target.value })}
                placeholder="https://api.openai.com/v1/chat/completions"
                className="font-mono"
                required
              />
            </PanelField>
            <div className="grid grid-cols-2 gap-2">
              <PanelField label="模型 ID">
                <Input
                  value={apiForm.model_name}
                  onChange={(e) => setApiForm({ ...apiForm, model_name: e.target.value })}
                  placeholder="gpt-4o-2024-08-06"
                  className="font-mono"
                />
              </PanelField>
              <PanelField label="API 密钥">
                <Input
                  type="password"
                  value={apiForm.api_key}
                  onChange={(e) => setApiForm({ ...apiForm, api_key: e.target.value })}
                  placeholder="sk-..."
                  className="font-mono"
                />
              </PanelField>
            </div>
            <PanelField label="描述">
              <Input
                value={apiForm.description}
                onChange={(e) => setApiForm({ ...apiForm, description: e.target.value })}
                placeholder="备注（可选）"
              />
            </PanelField>
            <div className="pt-1">
              <Button type="submit" className="w-full" disabled={create.isPending}>
                {create.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                {create.isPending ? "添加中..." : "添加模型"}
              </Button>
            </div>
          </form>
        </TabsContent>

        {/* ── Self-Hosted Model ── */}
        <TabsContent value="selfhosted">
          <form onSubmit={handleCreateAndDeploy} className="space-y-3">
            {/* Model source */}
            <PanelField label="模型来源" required>
              <Select value={shForm.source} onValueChange={(v) => setShForm({ ...shForm, source: v as "huggingface" | "modelscope" })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="huggingface">HuggingFace</SelectItem>
                  <SelectItem value="modelscope">ModelScope</SelectItem>
                </SelectContent>
              </Select>
            </PanelField>
            <PanelField label="模型 ID" required>
              <div className="flex gap-2">
                <Input
                  value={shForm.model_id}
                  onChange={(e) => {
                    setShForm({ ...shForm, model_id: e.target.value });
                    setPreflightResult(null);
                  }}
                  placeholder="Qwen/Qwen2.5-7B-Instruct 或 https://huggingface.co/..."
                  className="font-mono flex-1"
                  required
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    if (!shForm.model_id) return;
                    try {
                      const result = await preflight.mutateAsync({
                        source: shForm.source,
                        model_id: shForm.model_id,
                      });
                      setPreflightResult(result);
                      if (result.ok && result.repo) {
                        setShForm((f) => ({
                          ...f,
                          model_id: result.repo!,
                          name: f.name || result.repo!.split("/").pop() || "",
                        }));
                      }
                    } catch {
                      setPreflightResult({
                        ok: false,
                        error: "预检请求失败",
                      });
                    }
                  }}
                  disabled={preflight.isPending || !shForm.model_id}
                >
                  {preflight.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Search className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
              {preflightResult && (
                <div
                  className={`mt-2 rounded-md border p-2 text-[11px] ${
                    preflightResult.ok
                      ? "bg-muted/30"
                      : "bg-destructive/10 text-destructive"
                  }`}
                >
                  {!preflightResult.ok ? (
                    <p>{preflightResult.error}</p>
                  ) : (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-medium">
                          {preflightResult.repo}
                        </span>
                        {preflightResult.url && (
                          <a
                            href={preflightResult.url}
                            target="_blank"
                            rel="noopener"
                            className="text-primary hover:underline inline-flex items-center gap-1"
                          >
                            打开 <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-x-3 text-muted-foreground">
                        {preflightResult.license && (
                          <div>
                            <span>License: </span>
                            <span className="font-mono text-foreground">
                              {preflightResult.license}
                            </span>
                          </div>
                        )}
                        {preflightResult.pipeline_tag && (
                          <div>
                            <span>任务: </span>
                            <span className="font-mono text-foreground">
                              {preflightResult.pipeline_tag}
                            </span>
                          </div>
                        )}
                        {preflightResult.downloads !== undefined && (
                          <div>
                            <span>下载: </span>
                            <span className="font-mono text-foreground">
                              {preflightResult.downloads.toLocaleString()}
                            </span>
                          </div>
                        )}
                        {preflightResult.estimated_size_bytes !== undefined &&
                          preflightResult.estimated_size_bytes > 0 && (
                          <div>
                            <span>估计大小: </span>
                            <span className="font-mono text-foreground">
                              {(
                                preflightResult.estimated_size_bytes /
                                1024 ** 3
                              ).toFixed(2)}{" "}
                              GB
                            </span>
                          </div>
                        )}
                      </div>
                      {preflightResult.tags && preflightResult.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {preflightResult.tags.map((t) => (
                            <span
                              key={t}
                              className="px-1.5 py-0.5 rounded bg-background border text-[10px]"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </PanelField>

            {/* Token status */}
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              {tokenSet ? (
                <><Check className="h-3 w-3 text-emerald-500" /><span>{tokenLabel} 已配置</span></>
              ) : (
                <><XIcon className="h-3 w-3 text-muted-foreground/50" /><span>{tokenLabel} 未配置（私有模型需要）</span></>
              )}
              <span>·</span>
              <a href={accountHref} className="text-primary hover:underline">去设置</a>
            </div>

            <PanelField label="显示名称">
              <Input
                value={shForm.name}
                onChange={(e) => setShForm({ ...shForm, name: e.target.value })}
                placeholder={shForm.model_id.split("/").pop() || "自动使用模型 ID"}
              />
            </PanelField>

            {/* ── Deployment config (integrated) ── */}
            <div className="rounded-md border p-3 space-y-3">
              <p className="text-xs font-medium">集群部署</p>
              <PanelField label="计算集群" required>
                <Select value={shForm.cluster_id} onValueChange={(v) => setShForm({ ...shForm, cluster_id: v })}>
                  <SelectTrigger><SelectValue placeholder="选择集群" /></SelectTrigger>
                  <SelectContent>
                    {clusters.length === 0 ? (
                      <div className="px-3 py-4 text-center text-xs text-muted-foreground">
                        暂无集群，<a href="/clusters" className="text-primary hover:underline">去添加</a>
                      </div>
                    ) : clusters.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
                        <span className="text-muted-foreground ml-1">
                          {c.gpu_count > 0 ? `${c.gpu_count} GPU` : "CPU"}
                          {c.gpu_type ? ` (${c.gpu_type})` : ""}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </PanelField>
              <div className="grid grid-cols-2 gap-2">
                <PanelField label="GPU 数量">
                  <Input
                    type="number" min="0"
                    value={shForm.gpu_count}
                    onChange={(e) => setShForm({ ...shForm, gpu_count: e.target.value })}
                    className="font-mono"
                  />
                  <p className="text-[10px] text-muted-foreground mt-0.5">0 = CPU 模式</p>
                </PanelField>
                <PanelField label="内存 (GB)">
                  <Input
                    type="number" min="4"
                    value={shForm.memory_gb}
                    onChange={(e) => setShForm({ ...shForm, memory_gb: e.target.value })}
                    className="font-mono"
                  />
                </PanelField>
              </div>
            </div>

            {/* Errors */}
            {deployError && (
              <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
                {deployError}
              </div>
            )}

            {/* Submit */}
            <div className="pt-1">
              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting || !shForm.model_id || !shForm.cluster_id}
              >
                {isSubmitting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Server className="mr-2 h-4 w-4" />
                )}
                {deployPhase === "creating" ? "注册模型中..." :
                 deployPhase === "deploying" ? "部署到集群中..." :
                 "注册并部署"}
              </Button>
              <p className="text-[10px] text-muted-foreground mt-1.5 text-center">
                模型将注册到平台并自动部署 vLLM 到选定集群
              </p>
            </div>
          </form>
        </TabsContent>
      </Tabs>
    </>
  );
}
