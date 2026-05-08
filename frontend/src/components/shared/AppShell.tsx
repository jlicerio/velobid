import { useState, useRef, useEffect, useCallback } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ChatPanel } from "@/components/chat/chat-panel";
import { useChat } from "@/lib/chat-store";
import { logout } from "@/api/services/auth";
import { fetchProjectsWithPricing } from "@/api/services/projects";

const navItems = [
  { to: "/projects", label: "Projects", icon: "📋" },
  { to: "/residential", label: "Residential", icon: "🏠" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export function AppShell() {
  const [sidebarWidth, setSidebarWidth] = useState(400);
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { state, dispatch, createSession } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  // Detect mobile and auto-toggle sidebar
  useEffect(() => {
    const check = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      setSidebarOpen(!mobile);
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // Detect project context from route
  const projectMatch = location.pathname.match(/^\/projects\/([^/]+)/);
  const currentProjectId = projectMatch ? projectMatch[1] : null;

  // Track previous project context so we can restore sessions
  const prevProjectRef = useRef<string | null>(null);

  // When project context changes, switch session
  useEffect(() => {
    prevProjectRef.current = currentProjectId;

    // Set project context in store
    dispatch({ type: "SET_PROJECT", id: currentProjectId || "" });

    // Find existing session for this context, or create one
    const sessions = Object.values(state.sessions);
    const matchingSession = sessions.find(
      (s) => s.projectId === (currentProjectId || "")
    );

    if (matchingSession) {
      dispatch({ type: "SET_SESSION", id: matchingSession.id });
    } else {
      // Create a new session for this context
      const newSessionId = createSession(currentProjectId || undefined);
      dispatch({ type: "SET_SESSION", id: newSessionId });
    }
  }, [currentProjectId]);

  useEffect(() => {
    if (currentProjectId) return;

    let cancelled = false;

    async function injectDashboardContext() {
      const sessionId = state.currentSessionId;
      if (!sessionId) return;

      const session = state.sessions[sessionId];
      const hasDashboardContext = session?.messages.some(
        (message) =>
          message.role === "system" &&
          message.content.includes("[dashboard-context]"),
      );

      if (hasDashboardContext) return;

      try {
        const projects = await fetchProjectsWithPricing();
        if (cancelled) return;

        const active = projects.filter((p) => !p.archived);
        const archived = projects.filter((p) => p.archived);
        const totalBid = projects.reduce((sum, p) => sum + (p.total_bid || 0), 0);
        const totalLaborHours = projects.reduce(
          (sum, p) => sum + (p.total_labor_hours || 0),
          0,
        );
        const totalMaterial = projects.reduce(
          (sum, p) => sum + (p.total_material || 0),
          0,
        );

        const topProjects = [...projects]
          .sort((a, b) => (b.total_bid || 0) - (a.total_bid || 0))
          .slice(0, 5)
          .map(
            (project) =>
              `- ${project.name} | ${project.trade || "unknown"} | ${project.city || "?"}, ${project.state || "?"} | bid ${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(project.total_bid || 0)} | labor ${project.total_labor_hours?.toLocaleString() ?? "—"} hrs`,
          );

        const dashboardContext = [
          "[dashboard-context] You are helping the user manage the full VeloBid projects dashboard.",
          "Answer using the portfolio context below when the user asks about projects, totals, status, labor hours, or management actions.",
          "",
          `Portfolio summary: ${projects.length} projects total, ${active.length} active, ${archived.length} archived.`,
          `Portfolio totals: bid ${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(totalBid)}, labor hours ${totalLaborHours.toLocaleString(undefined, { maximumFractionDigits: 1 })}, materials ${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(totalMaterial)}.`,
          "",
          "Available dashboard tools:",
          "- Search and filter projects",
          "- Sort by name, bid value, labor cost, labor hours, or area",
          "- Archive or unarchive a project",
          "- Open a project to review line items and detailed bid data",
          "- Refresh the portfolio totals",
          "",
          "Top projects:",
          ...topProjects,
          "",
          "If the user asks for an overview, summarize the portfolio. If they ask for a project-specific detail, ask which project they mean or use the best matching project from the current view.",
        ].join("\n");

        dispatch({
          type: "ADD_MESSAGE",
          sessionId,
          message: {
            id: `dashboard-context-${Date.now()}`,
            role: "system",
            content: dashboardContext,
            timestamp: Date.now(),
          },
        });
      } catch {
        // Dashboard context is helpful, but never block the UI if the fetch fails.
      }
    }

    void injectDashboardContext();

    return () => {
      cancelled = true;
    };
  }, [currentProjectId, state.currentSessionId, state.sessions, dispatch]);

  // Resize handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    setSidebarWidth(Math.max(320, Math.min(800, e.clientX)));
  }, [isResizing]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    }
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Chat Sidebar — persistent on desktop, overlay on mobile */}
      <div
        ref={sidebarRef}
        style={{ width: isMobile ? undefined : sidebarWidth }}
        className={cn(
          "flex flex-col border-r bg-card",
          isMobile
            ? "fixed inset-y-0 left-0 z-50 w-[85vw] max-w-[400px] transition-transform duration-200"
            : "relative shrink-0",
          isMobile && !sidebarOpen && "hidden"
        )}
      >
        <div className="h-12 border-b flex items-center px-4 gap-2 shrink-0">
          {isMobile && (
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-sm mr-1 hover:bg-accent rounded p-1"
              aria-label="Close sidebar"
            >
              ←
            </button>
          )}
          <span className="text-base">💬</span>
          <span className="text-sm font-semibold">AI Assistant</span>
          {currentProjectId && (
            <span className="ml-auto text-[11px] bg-primary/10 text-primary px-2 py-0.5 rounded-full truncate max-w-[120px]">
              {currentProjectId}
            </span>
          )}
        </div>
        <div className="flex-1 overflow-hidden">
          <ChatPanel />
        </div>
      </div>

      {/* Mobile backdrop */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Resize handle */}
      <div
        onMouseDown={handleMouseDown}
        className="w-1 hover:w-1.5 bg-border hover:bg-primary/50 cursor-col-resize transition-all shrink-0 relative z-10"
      />

      {/* Right side — Nav + Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top navigation */}
        <header className="h-12 border-b flex items-center px-4 gap-2 shrink-0 bg-card">
          {/* Mobile hamburger toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden text-lg px-1 hover:bg-accent rounded"
            aria-label="Toggle chat sidebar"
          >
            ☰
          </button>
          <NavLink to="/" className="text-sm font-bold text-primary mr-4">
            VeloBid
          </NavLink>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/projects"}
                className={({ isActive }) =>
                  cn(
                    "px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )
                }
              >
                {item.icon} {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            {currentProjectId ? (
              <span className="text-primary font-medium text-xs">Project view</span>
            ) : (
              <span className="text-xs text-muted-foreground">Dashboard</span>
            )}
            <button
              onClick={logout}
              className="text-xs text-muted-foreground hover:text-destructive transition-colors px-2 py-1 rounded hover:bg-destructive/10"
            >
              Log out
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
