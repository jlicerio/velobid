import { useParams } from "react-router-dom";
export function DocumentViewerPage() {
  const { projectId } = useParams();
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Documents</h1>
      <p className="text-muted-foreground">Project: {projectId}</p>
      <p className="text-muted-foreground mt-2">Document viewer coming soon.</p>
    </div>
  );
}
