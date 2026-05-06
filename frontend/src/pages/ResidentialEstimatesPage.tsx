import { useState } from "react";
import { createEstimate } from "@/api/services/residential";

export function ResidentialEstimatesPage() {
  const [form, setForm] = useState({
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
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function updateField(
    field: string,
    value: string | boolean | { item: string; cost: number }[] | { item: string; hours: number }[]
  ) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    const payload = {
      ...form,
      property_sqft: form.property_sqft ? parseFloat(form.property_sqft) : undefined,
      equipment: form.equipment.length > 0 ? form.equipment : undefined,
      labor_tasks: form.labor_tasks.length > 0 ? form.labor_tasks : undefined,
    };

    try {
      const data = await createEstimate(payload);
      setResult(JSON.stringify(data, null, 2));
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null
            ? JSON.stringify(err)
            : String(err);
      setResult("Error: " + message);
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

      {result && (
        <div className="mt-6">
          {result.startsWith("Error:") ? (
            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
              {result}
            </div>
          ) : (
            <pre className="p-4 bg-muted rounded-lg text-xs overflow-auto max-h-96">{result}</pre>
          )}
        </div>
      )}
    </div>
  );
}
