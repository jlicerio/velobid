import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSettings, patchSettings } from "@/api/services/settings";
import {
  fetchIntegrationStatus,
  initiateOAuth,
  disconnectIntegration,
  getToolkitLabel,
  getToolkitIcon,
  type IntegrationStatus,
} from "@/api/services/integrations";

interface CompanySettings {
  name: string;
  address: string;
  phone: string;
  email: string;
  license_number: string;
}
interface PricingSettings {
  default_contingency_pct: number;
  default_overhead_profit_pct: number;
  default_equipment_markup_pct: number;
  default_labor_rate: number;
  default_tax_rate: number;
  default_permit_fee: number;
  default_misc_material_pct: number;
}
interface AgentSettings {
  model: string;
  temperature: number;
  company_context: string;
}

export function SettingsPage() {
  const [company, setCompany] = useState<CompanySettings | null>(null);
  const [pricing, setPricing] = useState<PricingSettings | null>(null);
  const [agent, setAgent] = useState<AgentSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [dirty, setDirty] = useState(false);

  // Integrations state
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);
  const [integrationsLoading, setIntegrationsLoading] = useState(true);
  const [connectingToolkit, setConnectingToolkit] = useState<string | null>(
    null,
  );
  const [integrationMsg, setIntegrationMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings()
      .then((d) => {
        setCompany(d.company);
        setPricing(d.pricing);
        setAgent(d.agent);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        setFetchError(true);
      });

    // Load integration statuses
    const bidderId = localStorage.getItem("bidder_id") || "";
    if (bidderId) {
      fetchIntegrationStatus(bidderId)
        .then((res) => {
          setIntegrations(res.integrations);
          setIntegrationsLoading(false);
        })
        .catch(() => {
          setIntegrationsLoading(false);
        });
    } else {
      setIntegrationsLoading(false);
    }
  }, []);

  const patch = useCallback(
    async (section: string, key: string, value: any) => {
      setDirty(true);
      if (section === "company")
        setCompany((p) => (p ? { ...p, [key]: value } : p));
      else if (section === "pricing")
        setPricing((p) => (p ? { ...p, [key]: value } : p));
      else if (section === "agent")
        setAgent((p) => (p ? { ...p, [key]: value } : p));
    },
    [],
  );

  const handleSave = useCallback(async () => {
    setSaving(true);
    setMsg(null);
    try {
      const body: Record<string, any> = {};
      if (company) body.company = company;
      if (pricing) body.pricing = pricing;
      if (agent) body.agent = agent;
      const data = await patchSettings(body);
      setCompany(data.settings.company);
      setPricing(data.settings.pricing);
      setAgent(data.settings.agent);
      setMsg({ type: "success", text: "Settings saved" });
      setDirty(false);
      setTimeout(() => setMsg(null), 3000);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Save failed";
      setMsg({ type: "error", text: `Save failed: ${message}` });
    } finally {
      setSaving(false);
    }
  }, [company, pricing, agent]);

  // Integration handlers
  const handleConnect = useCallback(async (toolkit: string) => {
    const bidderId = localStorage.getItem("bidder_id") || "";
    if (!bidderId) return;
    setConnectingToolkit(toolkit);
    setIntegrationMsg(null);
    try {
      const res = await initiateOAuth({ toolkit, bidder_id: bidderId });
      if (res.redirect_url) {
        // Open OAuth in a popup/pop-under
        const popup = window.open(
          res.redirect_url,
          "velobid-oauth",
          "width=600,height=700",
        );
        // Poll for status after OAuth completes
        const pollInterval = setInterval(async () => {
          try {
            const status = await fetchIntegrationStatus(bidderId);
            const connected = status.integrations.find(
              (i) => i.toolkit === toolkit && i.status === "connected",
            );
            if (connected) {
              clearInterval(pollInterval);
              setIntegrations(status.integrations);
              setIntegrationMsg(`${getToolkitLabel(toolkit)} connected!`);
              setTimeout(() => setIntegrationMsg(null), 4000);
              setConnectingToolkit(null);
              popup?.close();
            }
          } catch {
            // Keep polling
          }
        }, 2000);
        // Stop polling after 2 minutes
        setTimeout(() => {
          clearInterval(pollInterval);
          setConnectingToolkit(null);
        }, 120_000);
      } else {
        setIntegrationMsg("OAuth initiation failed — check server config.");
        setConnectingToolkit(null);
      }
    } catch {
      setIntegrationMsg("Connection failed. Is Composio configured?");
      setConnectingToolkit(null);
    }
  }, []);

  const handleDisconnect = useCallback(async (toolkit: string) => {
    const bidderId = localStorage.getItem("bidder_id") || "";
    if (!bidderId) return;
    setIntegrationMsg(null);
    try {
      await disconnectIntegration({ toolkit, bidder_id: bidderId });
      const status = await fetchIntegrationStatus(bidderId);
      setIntegrations(status.integrations);
      setIntegrationMsg(`${getToolkitLabel(toolkit)} disconnected.`);
      setTimeout(() => setIntegrationMsg(null), 3000);
    } catch {
      setIntegrationMsg("Disconnect failed.");
    }
  }, []);

  useEffect(() => {
    if (!dirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  if (loading)
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-8 pb-16">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <div className="flex items-center gap-3">
          {msg && (
            <span
              className={`text-sm ${msg.type === "success" ? "text-green-600" : "text-destructive"}`}
            >
              {msg.text}
            </span>
          )}
          {dirty && !msg && (
            <span className="text-xs text-yellow-600 bg-yellow-50 dark:bg-yellow-950/20 px-2 py-1 rounded">
              Unsaved changes
            </span>
          )}
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>

      {fetchError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load settings. The server may be unavailable or the request
          timed out.
          <button
            onClick={() => {
              setFetchError(false);
              setLoading(true);
              fetchSettings()
                .then((d) => {
                  setCompany(d.company);
                  setPricing(d.pricing);
                  setAgent(d.agent);
                  setLoading(false);
                })
                .catch(() => {
                  setLoading(false);
                  setFetchError(true);
                });
            }}
            className="ml-3 underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Company */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Company</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="c-name">Company Name</Label>
            <Input
              id="c-name"
              value={company?.name ?? ""}
              onChange={(e) => patch("company", "name", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="c-license">License Number</Label>
            <Input
              id="c-license"
              value={company?.license_number ?? ""}
              onChange={(e) =>
                patch("company", "license_number", e.target.value)
              }
            />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="c-address">Address</Label>
            <Input
              id="c-address"
              value={company?.address ?? ""}
              onChange={(e) => patch("company", "address", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="c-phone">Phone</Label>
            <Input
              id="c-phone"
              value={company?.phone ?? ""}
              onChange={(e) => patch("company", "phone", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="c-email">Email</Label>
            <Input
              id="c-email"
              value={company?.email ?? ""}
              onChange={(e) => patch("company", "email", e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Pricing */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Pricing Defaults</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              key: "default_contingency_pct",
              label: "Contingency %",
              step: 0.1,
            },
            {
              key: "default_overhead_profit_pct",
              label: "Overhead & Profit %",
              step: 0.1,
            },
            {
              key: "default_equipment_markup_pct",
              label: "Equipment Markup %",
              step: 0.1,
            },
            {
              key: "default_labor_rate",
              label: "Labor Rate ($/hr)",
              step: 0.5,
            },
            { key: "default_tax_rate", label: "Tax Rate", step: 0.0001 },
            { key: "default_permit_fee", label: "Permit Fee ($)", step: 1 },
            {
              key: "default_misc_material_pct",
              label: "Misc Material %",
              step: 0.1,
            },
          ].map(({ key, label, step }) => (
            <div key={key} className="space-y-1.5">
              <Label htmlFor={`p-${key}`}>{label}</Label>
              <Input
                id={`p-${key}`}
                type="number"
                step={step}
                value={(pricing as any)?.[key] ?? ""}
                onChange={(e) =>
                  patch("pricing", key, parseFloat(e.target.value) || 0)
                }
              />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Agent */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AI Agent</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="a-model">Model</Label>
            <Input
              id="a-model"
              value={agent?.model ?? ""}
              onChange={(e) => patch("agent", "model", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="a-temp">Temperature</Label>
            <Input
              id="a-temp"
              type="number"
              step={0.05}
              min={0}
              max={2}
              value={agent?.temperature ?? 0.3}
              onChange={(e) =>
                patch("agent", "temperature", parseFloat(e.target.value) || 0)
              }
            />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="a-context">Company Context (system prompt)</Label>
            <Textarea
              id="a-context"
              rows={5}
              value={agent?.company_context ?? ""}
              onChange={(e) =>
                patch("agent", "company_context", e.target.value)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Integrations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Integrations</CardTitle>
            {integrationMsg && (
              <span className="text-xs text-green-600 bg-green-50 dark:bg-green-950/20 px-2 py-1 rounded">
                {integrationMsg}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {integrationsLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
              Loading integrations…
            </div>
          ) : integrations.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No integrations available. Set{" "}
              <code className="text-xs bg-muted px-1 rounded">
                COMPOSIO_API_KEY
              </code>{" "}
              to enable.
            </p>
          ) : (
            <div className="space-y-3">
              {integrations.map((integration) => (
                <div
                  key={integration.toolkit}
                  className="flex items-center justify-between py-2 px-3 rounded-lg border bg-card hover:bg-accent/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">
                      {getToolkitIcon(integration.toolkit)}
                    </span>
                    <div>
                      <p className="text-sm font-medium">
                        {getToolkitLabel(integration.toolkit)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {integration.status === "connected"
                          ? "Connected — Hermes can read and act on your behalf"
                          : integration.status === "not_configured"
                            ? "Not configured — set COMPOSIO_API_KEY"
                            : integration.status === "not_available"
                              ? "Unavailable — install composio-core"
                              : "Not connected — click to link your account"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {integration.status === "connected" ? (
                      <>
                        <span className="text-xs text-green-600 font-medium flex items-center gap-1">
                          <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
                          Active
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDisconnect(integration.toolkit)}
                        >
                          Disconnect
                        </Button>
                      </>
                    ) : integration.status === "not_connected" ? (
                      <Button
                        size="sm"
                        onClick={() => handleConnect(integration.toolkit)}
                        disabled={connectingToolkit === integration.toolkit}
                      >
                        {connectingToolkit === integration.toolkit ? (
                          <>
                            <div className="animate-spin h-3 w-3 border-2 border-current border-t-transparent rounded-full mr-1" />
                            Connecting…
                          </>
                        ) : (
                          "Connect"
                        )}
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        Unavailable
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
