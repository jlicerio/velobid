import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/services/auth";

export function LoginPage() {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await login(userId, password);
      if (data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("bidder_id", data.bidder_id);
        localStorage.setItem("user_id", userId);
        navigate("/projects");
      } else {
        setError("Authentication failed - no token received");
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Login failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm border rounded-xl p-8 bg-card shadow-sm">
        <h1 className="text-xl font-semibold mb-1">VeloBid</h1>
        <p className="text-sm text-muted-foreground mb-6">Sign in to your account</p>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">User ID</label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Enter your user ID"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Enter your password"
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <button
            type="submit"
            disabled={loading || !userId || !password}
            className="w-full py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
