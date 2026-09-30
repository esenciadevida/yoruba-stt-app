"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authAPI } from "@/lib/api";
import { isTokenExpired } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Shield, Lock, User, Loader2, Eye, EyeOff, AlertTriangle } from "lucide-react";

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    const user = localStorage.getItem("admin_user");
    if (token && user && !isTokenExpired(token)) {
      try {
        if (JSON.parse(user).is_admin) { router.push("/admin"); return; }
      } catch {}
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authAPI.adminLogin(username, password);
      if (!res.data.user.is_admin) {
        setError("Access denied. Admin privileges required.");
        setLoading(false);
        return;
      }
      localStorage.setItem("admin_token", res.data.access_token);
      localStorage.setItem("admin_user", JSON.stringify(res.data.user));
      router.push("/admin");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid credentials or insufficient privileges.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8 relative">
      <div className="absolute top-4 right-4"><ThemeToggle /></div>

      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-4 shadow-lg shadow-amber-500/20">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Admin Portal</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Authorized personnel only</p>
        </div>

        <div className="glass rounded-2xl p-8">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm flex items-center gap-2 animate-fade-in">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Username</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500"><User className="w-4 h-4" /></span>
                <input type="text" className="input-field" style={{ paddingLeft: "2.5rem" }} placeholder="Admin username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500"><Lock className="w-4 h-4" /></span>
                <input type={showPassword ? "text" : "password"} className="input-field" style={{ paddingLeft: "2.5rem", paddingRight: "2.5rem" }} placeholder="Admin password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors" tabIndex={-1}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading || !username || !password} className="btn-primary w-full flex items-center justify-center gap-2 mt-6">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Shield className="w-4 h-4" /> Sign In to Admin Portal</>}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-400 dark:text-slate-500 mt-6">
          This portal is restricted to authorized administrators.
        </p>
      </div>
    </div>
  );
}
