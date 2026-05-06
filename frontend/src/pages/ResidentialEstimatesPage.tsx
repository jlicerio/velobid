import { useState } from "react";
import { createEstimate } from "@/api/services/residential";

export function ResidentialEstimatesPage() {
  const [form, setForm] = useState({ project_name: "", square_footage: "", trade: "hvac" });
  const [result, setResult] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const data = await createEstimate(form);
      setResult(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setResult("Error: " + err.message);
    }
  }

  return (
    <div className="p-6 max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Residential Estimate</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Project Name</label>
          <input className="w-full px-3 py-2 border rounded-lg text-sm bg-background" value={form.project_name}
            onChange={(e) => setForm({ ...form, project_name: e.target.value })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Square Footage</label>
          <input className="w-full px-3 py-2 border rounded-lg text-sm bg-background" value={form.square_footage}
            onChange={(e) => setForm({ ...form, square_footage: e.target.value })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Trade</label>
          <select className="w-full px-3 py-2 border rounded-lg text-sm bg-background" value={form.trade}
            onChange={(e) => setForm({ ...form, trade: e.target.value })}>
            <option value="hvac">HVAC</option>
            <option value="electrical">Electrical</option>
            <option value="plumbing">Plumbing</option>
          </select>
        </div>
        <button type="submit" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm">Generate Estimate</button>
      </form>
      {result && <pre className="mt-4 p-4 bg-muted rounded-lg text-xs overflow-auto">{result}</pre>}
    </div>
  );
}
