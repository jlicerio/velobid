import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { LineItemsTable } from "@/features/bids/LineItemsTable";
import type { BidPreviewResponse, GeneratedFileResponse } from "@/types/bids";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchProjectsWithPricing } from "@/api/services/projects";
import { previewBid, generateBid } from "@/api/services/bids";

interface Project {
  id: string;
  name: string;
  location?: string;
  area_sf?: number;
  trade?: string;
  archived?: boolean;
  city?: string;
  state?: string;
}

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trade, setTrade] = useState("hvac");
  const [preview, setPreview] = useState<BidPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [bidResults, setBidResults] = useState<GeneratedFileResponse[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "bids" | "documents">("overview");
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    fetchProject();
  }, [projectId]);

  async function fetchProject() {
    setLoading(true);
    try {
      const all = await fetchProjectsWithPricing();
      const found = all.find((p) => p.id === projectId);
      if (found) setProject(found);
      else setError("Project not found");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const handlePreview = useCallback(async () => {
    if (!projectId) return;
    setPreviewLoading(true);
    setPreview(null);
    try {
      const data = await previewBid(projectId, trade);
      setPreview(data);
    } catch (e: any) {
      setPreview(null);
      alert(`Preview failed: ${e.message}`);
    } finally {
      setPreviewLoading(false);
    }
  }, [projectId, trade]);

  async function handleGenerate(pkg: string) {
    if (!projectId) return;
    setGenerating(true);
    try {
      const data = await generateBid(projectId, trade, pkg);
      if (data.generated_files) {
        setBidResults((prev) => [...prev, ...data.generated_files]);
      }
    } catch (e: any) {
      alert(`Generate failed: ${e.message}`);
    } finally {
      setGenerating(false);
    }
  }

  const fmt = (v?: number) => v != null ? `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
    </div>
  );

  if (error) return (
    <div className="p-6 text-destructive">
      <p>{error}</p>
      <button onClick={() => navigate("/projects")} className="mt-4 px-4 py-2 border rounded-lg text-sm hover:bg-accent">
        Back to Projects
      </button>
    </div>
  );

  if (!project) return null;

  return (
    <div className="flex h-full">
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b px-6 py-4">
          <button onClick={() => navigate("/projects")} className="text-sm text-muted-foreground hover:text-foreground mb-2 block">
            &larr; Back to Projects
          </button>
          <h1 className="text-xl font-bold">{project.name}</h1>
          {(project.city || project.state) && (
            <p className="text-sm text-muted-foreground">{project.city}{project.city && project.state ? ", " : ""}{project.state}</p>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b px-6 gap-4">
          {(["overview", "bids", "documents"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === "overview" && (
            <div className="space-y-6 max-w-4xl">
              {/* Project stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="border rounded-lg p-4">
                  <label className="text-xs text-muted-foreground">Trade</label>
                  <p className="text-lg font-semibold mt-1">{project.trade ? project.trade.toUpperCase() : "—"}</p>
                </div>
                {project.area_sf && (
                  <div className="border rounded-lg p-4">
                    <label className="text-xs text-muted-foreground">Area</label>
                    <p className="text-lg font-semibold mt-1">{project.area_sf.toLocaleString()} SF</p>
                  </div>
                )}
              </div>

              {/* Trade selector + actions */}
              <div>
                <label className="block text-sm font-medium mb-2">Trade</label>
                <div className="flex flex-wrap items-center gap-2">
                  <select value={trade} onChange={(e) => setTrade(e.target.value)}
                    className="px-3 py-2 border rounded-lg text-sm bg-background">
                    <option value="hvac">HVAC</option>
                    <option value="electrical">Electrical</option>
                    <option value="plumbing">Plumbing</option>
                  </select>
                  <Button variant="outline" size="sm" onClick={handlePreview} disabled={previewLoading}>
                    {previewLoading ? "Loading..." : "Preview Bid"}
                  </Button>
                  <Button size="sm" onClick={() => handleGenerate("client")} disabled={generating}>
                    {generating ? "Generating..." : "Generate Client Bid"}
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleGenerate("internal")} disabled={generating}>
                    {generating ? "Generating..." : "Generate Internal Bid"}
                  </Button>
                </div>
              </div>

              {/* Preview results */}
              {preview && (
                <div className="space-y-6">
                  {/* Bid totals summary */}
                  <div className="border rounded-lg p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-sm">Bid Summary</h3>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{preview.trade_name}</Badge>
                        <Badge>{preview.status}</Badge>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="text-xs text-muted-foreground">Total Bid</label>
                        <p className="text-xl font-bold text-primary">{fmt(preview.totals.total_bid_amount)}</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Direct Cost</label>
                        <p className="text-lg font-semibold">{fmt(preview.totals.total_direct_cost)}</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Material</label>
                        <p className="text-lg font-semibold">{fmt(preview.totals.total_material)}</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Labor</label>
                        <p className="text-lg font-semibold">{fmt(preview.totals.total_labor)}</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Labor Hours</label>
                        <p className="text-lg font-semibold">{preview.totals.total_labor_hours.toLocaleString()} hrs</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Contingency ({preview.totals.contingency_pct}%)</label>
                        <p className="text-lg font-semibold">{fmt(preview.totals.contingency)}</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">Overhead & Profit ({preview.totals.overhead_profit_pct}%)</label>
                        <p className="text-lg font-semibold">{fmt(preview.totals.overhead_profit)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Line items */}
                  {preview.line_items.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-sm mb-3">Line Items ({preview.line_items.length})</h3>
                      <LineItemsTable lineItems={preview.line_items} compact />
                    </div>
                  )}

                  {/* Exclusions */}
                  {preview.exclusions.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-sm mb-2">Exclusions</h3>
                      <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                        {preview.exclusions.map((ex, i) => <li key={i}>{ex}</li>)}
                      </ul>
                    </div>
                  )}

                  {/* Validation */}
                  {preview.validation.length > 0 && (
                    <div className="border border-yellow-300 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg p-4">
                      <h3 className="font-semibold text-sm mb-2 text-yellow-800 dark:text-yellow-300">
                        Validation Issues ({preview.validation.length})
                      </h3>
                      <ul className="space-y-1 text-sm">
                        {preview.validation.map((v, i) => (
                          <li key={i}><strong>{v.field}:</strong> {v.message}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Raw JSON toggle */}
                  <div className="pt-2">
                    <button onClick={() => setShowRaw(!showRaw)} className="text-xs text-muted-foreground hover:text-foreground underline">
                      {showRaw ? "Hide JSON" : "Show raw JSON"}
                    </button>
                    {showRaw && (
                      <pre className="mt-2 p-4 bg-muted rounded-lg text-xs overflow-auto max-h-96">
                        {JSON.stringify(preview, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "bids" && (
            <div className="text-center text-muted-foreground py-12 space-y-3">
              <p>Bid management — versions, diffs, and line items</p>
              {bidResults.length > 0 && (
                <div className="max-w-md mx-auto text-left space-y-2">
                  <h3 className="font-medium text-sm">Generated Files</h3>
                  {bidResults.map((r, i) => (
                    <div key={i} className="text-sm border rounded-lg p-3 flex items-center justify-between">
                      <span>{r.filename}</span>
                      <a href={r.url} target="_blank" className="text-primary hover:underline text-xs">View PDF</a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "documents" && (
            <div className="text-center text-muted-foreground py-12">
              <p>Document viewer — blueprints and PDFs</p>
              <button
                onClick={() => navigate(`/projects/${projectId}/documents`)}
                className="mt-4 px-4 py-2 border rounded-lg text-sm hover:bg-accent"
              >
                Open Documents
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
