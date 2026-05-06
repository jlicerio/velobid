import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSettings, patchSettings } from "@/api/services/settings";

interface CompanySettings {
  name: string; address: string; phone: string; email: string; license_number: string;
}
interface PricingSettings {
  default_contingency_pct: number; default_overhead_profit_pct: number;
  default_equipment_markup_pct: number; default_labor_rate: number;
  default_tax_rate: number; default_permit_fee: number; default_misc_material_pct: number;
}
interface AgentSettings {
  model: string; temperature: number; company_context: string;
}

export function SettingsPage() {
  const [company, setCompany] = useState<CompanySettings | null>(null);
  const [pricing, setPricing] = useState<PricingSettings | null>(null);
  const [agent, setAgent] = useState<AgentSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    fetchSettings()
      .then((d) => {
        setCompany(d.company);
        setPricing(d.pricing);
        setAgent(d.agent);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const patch = useCallback(async (section: string, key: string, value: any) => {
    // Optimistic local update
    if (section === "company") setCompany((p) => p ? { ...p, [key]: value } : p);
    else if (section === "pricing") setPricing((p) => p ? { ...p, [key]: value } : p);
    else if (section === "agent") setAgent((p) => p ? { ...p, [key]: value } : p);
  }, []);

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
      setTimeout(() => setMsg(null), 3000);
    } catch (e: any) {
      setMsg({ type: "error", text: `Save failed: ${e.message}` });
    } finally {
      setSaving(false);
    }
  }, [company, pricing, agent]);

  if (loading) return (
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
            <span className={`text-sm ${msg.type === "success" ? "text-green-600" : "text-destructive"}`}>
              {msg.text}
            </span>
          )}
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>

      {/* Company */}
      <Card>
        <CardHeader><CardTitle className="text-lg">Company</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="c-name">Company Name</Label>
            <Input id="c-name" value={company?.name ?? ""} onChange={(e) => patch("company", "name", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="c-license">License Number</Label>
            <Input id="c-license" value={company?.license_number ?? ""} onChange={(e) => patch("company", "license_number", e.target.value)} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="c-address">Address</Label>
            <Input id="c-address" value={company?.address ?? ""} onChange={(e) => patch("company", "address", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="c-phone">Phone</Label>
            <Input id="c-phone" value={company?.phone ?? ""} onChange={(e) => patch("company", "phone", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="c-email">Email</Label>
            <Input id="c-email" value={company?.email ?? ""} onChange={(e) => patch("company", "email", e.target.value)} />
          </div>
        </CardContent>
      </Card>

      {/* Pricing */}
      <Card>
        <CardHeader><CardTitle className="text-lg">Pricing Defaults</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { key: "default_contingency_pct", label: "Contingency %", step: 0.1 },
            { key: "default_overhead_profit_pct", label: "Overhead & Profit %", step: 0.1 },
            { key: "default_equipment_markup_pct", label: "Equipment Markup %", step: 0.1 },
            { key: "default_labor_rate", label: "Labor Rate ($/hr)", step: 0.5 },
            { key: "default_tax_rate", label: "Tax Rate", step: 0.0001 },
            { key: "default_permit_fee", label: "Permit Fee ($)", step: 1 },
            { key: "default_misc_material_pct", label: "Misc Material %", step: 0.1 },
          ].map(({ key, label, step }) => (
            <div key={key} className="space-y-1.5">
              <Label htmlFor={`p-${key}`}>{label}</Label>
              <Input
                id={`p-${key}`}
                type="number"
                step={step}
                value={(pricing as any)?.[key] ?? ""}
                onChange={(e) => patch("pricing", key, parseFloat(e.target.value) || 0)}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Agent */}
      <Card>
        <CardHeader><CardTitle className="text-lg">AI Agent</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="a-model">Model</Label>
            <Input id="a-model" value={agent?.model ?? ""} onChange={(e) => patch("agent", "model", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="a-temp">Temperature</Label>
            <Input id="a-temp" type="number" step={0.05} min={0} max={2}
              value={agent?.temperature ?? 0.3}
              onChange={(e) => patch("agent", "temperature", parseFloat(e.target.value) || 0)} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="a-context">Company Context (system prompt)</Label>
            <Textarea id="a-context" rows={5}
              value={agent?.company_context ?? ""}
              onChange={(e) => patch("agent", "company_context", e.target.value)} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
