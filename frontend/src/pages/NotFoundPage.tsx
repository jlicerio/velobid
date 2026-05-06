import { Link } from "react-router-dom";
export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found</p>
      <Link to="/projects" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm">Go to Projects</Link>
    </div>
  );
}
