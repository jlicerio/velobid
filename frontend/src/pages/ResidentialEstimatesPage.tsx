import { useState } from "react";
import { Link } from "react-router-dom";
import { createEstimate, type ResidentialEstimateResponse } from "@/api/services/residential";

type EstimateFormState = {
  customer_name: string;
  customer_address: string;
  customer_phone: string;
  customer_email: string;
  property_sqft: string;
  scope_description: string;
  equipment: { item: string; cost: number }[];
  labor_tasks: { item: string; hours: number }[];
  generate_pdf: boolean;
};

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

export function ResidentialEstimatesPage() {
  const [form, setForm] = useState<EstimateFormState>({
    customer_name: "",
    customer_address: "",
    customer_phone: "",
    customer_email: "",
    property_sqft: "",
    scope_description: "",
    equipment: [] as { item: string; cost: number }[],
    labor_tasks: [] as { item: string; hours: number }[],
    generate_pdf: true,
  });
  const [result, setResult] = useState<ResidentialEstimateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function updateField<K extends keyof EstimateFormState>(field: K, value: EstimateFormState[K]) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function formatCurrency(value: number | undefined) {
    return currencyFormatter.format(value ?? 0);
  }

  function formatPercent(value: number | undefined) {
    return `${((value ?? 0) * 100).toFixed(2)}%`;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const cleanedEquipment = form.equipment.filter((item) => item.item.trim().length > 0);
    const cleanedLaborTasks = form.labor_tasks.filter((task) => task.item.trim().length > 0);

    const payload = {
      ...form,
      property_sqft: form.property_sqft ? parseFloat(form.property_sqft) : undefined,
      equipment: cleanedEquipment.length > 0 ? cleanedEquipment : undefined,
      labor_tasks: cleanedLaborTasks.length > 0 ? cleanedLaborTasks : undefined,
    };

    try {
      const data = await createEstimate(payload);
      setResult(data);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null
            ? JSON.stringify(err)
            : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Residential Estimate</h1>
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Customer Name (required) */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Customer Name <span className="text-destructive">*</span>
          </label>
          <input
            className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
            placeholder="John Smith"
            value={form.customer_name}
            onChange={(e) => updateField("customer_name", e.target.value)}
            required
          />
        </div>

        {/* Customer Address (required) */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Customer Address <span className="text-destructive">*</span>
          </label>
          <input
            className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
            placeholder="123 Main St, McAllen TX"
            value={form.customer_address}
            onChange={(e) => updateField("customer_address", e.target.value)}
            required
          />
        </div>

        {/* Customer Phone (optional) */}
        <div>
          <label className="block text-sm font-medium mb-1">Customer Phone (optional)</label>
          <input
            className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
            placeholder="(555) 123-4567"
            value={form.customer_phone}
            onChange={(e) => updateField("customer_phone", e.target.value)}
          />
        </div>

        {/* Customer Email (optional) */}
        <div>
          <label className="block text-sm font-medium mb-1">Customer Email (optional)</label>
          <input
            className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
            placeholder="john@example.com"
            type="email"
            value={form.customer_email}
            onChange={(e) => updateField("customer_email", e.target.value)}
          />
        </div>

        {/* Property Sq Ft (optional) */}
        <div>
          <label className="block text-sm font-medium mb-1">Property Sq Ft (optional)</label>
          <input
            className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
            placeholder="2500"
            type="number"
            min="0"
            value={form.property_sqft}
            onChange={(e) => updateField("property_sqft", e.target.value)}
          />
        </div>

        {/* Scope Description (required) */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Scope Description <span className="text-destructive">*</span>
          </label>
          <textarea
            className="w-full px-3 py-2 border rounded-lg text-sm bg-background min-h-[80px]"
            placeholder="Replace existing 4-ton split system..."
            value={form.scope_description}
            onChange={(e) => updateField("scope_description", e.target.value)}
            required
          />
        </div>

        {/* Equipment (optional) — single row */}
        <div>
          <label className="block text-sm font-medium mb-1">Equipment (optional)</label>
          <div className="flex gap-3 items-start">
            <div className="flex-1">
              <input
                className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
                placeholder="Item name"
                value={form.equipment[0]?.item ?? ""}
                onChange={(e) =>
                  updateField("equipment", [{ item: e.target.value, cost: form.equipment[0]?.cost ?? 0 }])
                }
              />
            </div>
            <div className="w-32">
              <input
                className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
                placeholder="Cost"
                type="number"
                min="0"
                step="0.01"
                value={form.equipment[0]?.cost ?? ""}
                onChange={(e) =>
                  updateField("equipment", [
                    { item: form.equipment[0]?.item ?? "", cost: e.target.value ? parseFloat(e.target.value) : 0 },
                  ])
                }
              />
            </div>
          </div>
        </div>

        {/* Labor Tasks (optional) — single row */}
        <div>
          <label className="block text-sm font-medium mb-1">Labor Tasks (optional)</label>
          <div className="flex gap-3 items-start">
            <div className="flex-1">
              <input
                className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
                placeholder="Task name"
                value={form.labor_tasks[0]?.item ?? ""}
                onChange={(e) =>
                  updateField("labor_tasks", [{ item: e.target.value, hours: form.labor_tasks[0]?.hours ?? 0 }])
                }
              />
            </div>
            <div className="w-32">
              <input
                className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
                placeholder="Hours"
                type="number"
                min="0"
                step="0.5"
                value={form.labor_tasks[0]?.hours ?? ""}
                onChange={(e) =>
                  updateField("labor_tasks", [
                    { item: form.labor_tasks[0]?.item ?? "", hours: e.target.value ? parseFloat(e.target.value) : 0 },
                  ])
                }
              />
            </div>
          </div>
        </div>

        {/* Generate PDF */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="generate-pdf"
            className="h-4 w-4 rounded border-gray-300"
            checked={form.generate_pdf}
            onChange={(e) => updateField("generate_pdf", e.target.checked)}
          />
          <label htmlFor="generate-pdf" className="text-sm font-medium">
            Generate PDF
          </label>
        </div>

        <button
          type="submit"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Generating..." : "Generate Estimate"}
        </button>
      </form>

      {error && (
        <div className="mt-6 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
          Error: {error}
        </div>
      )}

      {result && (
        <div className="mt-6">
          <div className="rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-emerald-900 mb-4">
            <p className="text-sm font-semibold">Estimate created successfully</p>
            <p className="text-sm mt-1">
              Project <span className="font-semibold">{result.project_id}</span> for {result.customer_name} is ready.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border bg-card p-4">
              <h2 className="text-base font-semibold mb-3">Summary</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Customer</dt>
                  <dd className="font-medium text-right">{result.customer_name}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Project ID</dt>
                  <dd className="font-medium text-right">{result.project_id}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Grand Total</dt>
                  <dd className="font-semibold text-right">{formatCurrency(result.grand_total)}</dd>
                </div>
              </dl>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  to={`/projects/${result.project_id}`}
                  className="px-3 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
                >
                  Open Project
                </Link>
                {result.pdf_url ? (
                  <a
                    href={result.pdf_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-2 border rounded-lg text-sm font-medium hover:bg-accent"
                  >
                    Open Proposal PDF
                  </a>
                ) : (
                  <span className="px-3 py-2 border rounded-lg text-sm text-muted-foreground">
                    PDF not generated
                  </span>
                )}
              </div>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <h2 className="text-base font-semibold mb-3">Pricing Breakdown</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Equipment</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.equipment_total)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Labor</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.labor_total)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Misc Materials</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.misc_materials)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Permit Fee</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.permit_fee)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Subtotal</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.subtotal)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Tax</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.tax)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Labor Hours</dt>
                  <dd className="font-medium">{(result.totals.labor_hours ?? 0).toFixed(2)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Labor Rate</dt>
                  <dd className="font-medium">{formatCurrency(result.totals.labor_rate)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Equipment Markup</dt>
                  <dd className="font-medium">{(result.totals.equipment_markup_pct ?? 0).toFixed(2)}%</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-muted-foreground">Tax Rate</dt>
                  <dd className="font-medium">{formatPercent(result.totals.tax_rate)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3 border-t pt-2">
                  <dt className="font-semibold">Grand Total</dt>
                  <dd className="font-semibold">{formatCurrency(result.totals.grand_total ?? result.grand_total)}</dd>
                </div>
              </dl>
            </div>
          </div>

          {result.line_items.length > 0 ? (
            <div className="mt-4 rounded-lg border bg-card p-4">
              <h2 className="text-base font-semibold mb-3">Line Items</h2>
              <div className="space-y-3">
                {result.line_items.map((item, index) => (
                  <div key={`${item.type}-${item.description}-${index}`} className="rounded-md border p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium">{item.description}</p>
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mt-0.5">{item.type}</p>
                        {item.detail ? <p className="text-xs text-muted-foreground mt-1">{item.detail}</p> : null}
                        {item.hours !== undefined && item.rate !== undefined ? (
                          <p className="text-xs text-muted-foreground mt-1">
                            {item.hours.toFixed(2)} hrs at {formatCurrency(item.rate)}/hr
                          </p>
                        ) : null}
                        {item.cost !== undefined && item.markup !== undefined ? (
                          <p className="text-xs text-muted-foreground mt-1">
                            Base {formatCurrency(item.cost)} + markup {formatCurrency(item.markup)}
                          </p>
                        ) : null}
                      </div>
                      <div className="text-sm font-semibold shrink-0">{formatCurrency(item.total)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-lg border bg-card p-4 text-sm text-muted-foreground">No line items returned.</div>
          )}
        </div>
      )}
    </div>
  );
}
