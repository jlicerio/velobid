import { useParams } from "react-router-dom";
export function BlueprintVisionPage() {
  const { projectId } = useParams();
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Blueprint Vision Analysis</h1>
      <p className="text-muted-foreground">Project: {projectId}</p>
      <p className="text-muted-foreground mt-2">Vision analysis coming soon.</p>
    </div>
  );
}
