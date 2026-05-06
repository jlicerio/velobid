import { useState, useRef, useEffect, useCallback } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ChatPanel } from "@/components/chat/chat-panel";
import { useChat } from "@/lib/chat-store";
import { logout } from "@/api/services/auth";

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
  const { state, dispatch, createSession } = useChat();

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
      {/* Chat Sidebar — persistent, resizable, context-aware */}
      <div
        ref={sidebarRef}
        style={{ width: sidebarWidth }}
        className="flex flex-col border-r bg-card shrink-0 relative"
      >
        <div className="h-12 border-b flex items-center px-4 gap-2 shrink-0">
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

      {/* Resize handle */}
      <div
        onMouseDown={handleMouseDown}
        className="w-1 hover:w-1.5 bg-border hover:bg-primary/50 cursor-col-resize transition-all shrink-0 relative z-10"
      />

      {/* Right side — Nav + Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top navigation */}
        <header className="h-12 border-b flex items-center px-4 gap-2 shrink-0 bg-card">
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
