"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authAPI } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";
import { isTokenExpired } from "@/lib/api";
import { Mic, User, Lock, Mail, ArrowRight, Loader2, Eye, EyeOff, X } from "lucide-react";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [shakeError, setShakeError] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token && !isTokenExpired(token)) router.push("/dashboard");
  }, [router]);

  const resetForm = () => {
    setUsername("");
    setPassword("");
    setEmail("");
    setError("");
    setShowPassword(false);
  };

  const switchMode = (newMode: "login" | "register") => {
    setMode(newMode);
    resetForm();
  };

  const triggerShake = () => {
    setShakeError(true);
    setTimeout(() => setShakeError(false), 300);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        const res = await authAPI.register(username, password, email || undefined);
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("user", JSON.stringify(res.data.user));
        router.push("/dashboard");
      } else {
        const res = await authAPI.login(username, password);
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("user", JSON.stringify(res.data.user));
        router.push("/dashboard");
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Something went wrong";
      setError(msg);
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="relative z-10 text-center px-12">
          <div className="mb-8">
            <div className="w-24 h-24 mx-auto rounded-2xl bg-blue-600 flex items-center justify-center">
              <Mic className="w-12 h-12 text-white" />
            </div>
          </div>

          <h1 className="text-6xl font-extrabold mb-4 text-white">Bámi-Sọ̀rọ̀</h1>
          <p className="text-xl text-slate-400 mb-2">Bridging Languages, Preserving Culture</p>
          <p className="text-sm text-slate-500 mt-6 max-w-md mx-auto">
            Professional Yoruba speech recognition and translation powered by AI.
            Transcribe, translate, and preserve the beauty of Èdè Yorùbá.
          </p>

          <div className="flex flex-wrap gap-3 justify-center mt-10">
            {[
              { icon: "🎙️", label: "Local Yoruba speech recognition" },
              { icon: "🔀", label: "Mixed Yoruba/English auto-unified" },
              { icon: "✨", label: "Tone-perfect text output" },
              { icon: "🌍", label: "English ⇄ Yoruba translation" },
            ].map((f) => (
              <div
                key={f.label}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-slate-300 backdrop-blur-sm"
              >
                <span className="text-base leading-none">{f.icon}</span>
                <span>{f.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md relative">
          <div className="absolute top-4 right-4">
            <ThemeToggle />
          </div>

          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="w-16 h-16 mx-auto rounded-xl bg-blue-600 flex items-center justify-center mb-4">
              <Mic className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">Bámi-Sọ̀rọ̀</h1>
          </div>

          <div className={`rounded-2xl border border-slate-200 dark:border-white/10 p-8 ${shakeError ? "animate-shake" : ""}`}>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-foreground">
                {mode === "login" ? "Welcome back" : "Get started"}
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                {mode === "login"
                  ? "Sign in to continue"
                  : "Create your account to begin"}
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm flex items-center justify-between animate-fade-in">
                <span>{error}</span>
                <button onClick={() => setError("")} className="text-red-400 hover:text-red-300">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Username</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    className="input-field"
                    style={{ paddingLeft: "2.5rem" }}
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    minLength={3}
                    autoFocus
                  />
                </div>
              </div>

              {mode === "register" && (
                <div className="animate-fade-in">
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Email <span className="text-slate-400 dark:text-slate-500">(optional)</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none">
                      <Mail className="w-4 h-4" />
                    </span>
                    <input
                      type="email"
                      className="input-field"
                      style={{ paddingLeft: "2.5rem" }}
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Password</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none">
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    className="input-field"
                    style={{ paddingLeft: "2.5rem", paddingRight: "2.5rem" }}
                    placeholder={mode === "register" ? "Min 6 characters" : "Enter your password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {mode === "register" && password.length > 0 && (
                  <div className="mt-2 flex gap-1">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-colors ${
                          password.length >= i * 3
                            ? password.length >= 12
                              ? "bg-green-500"
                              : password.length >= 8
                              ? "bg-yellow-500"
                              : "bg-red-500"
                            : "bg-slate-200 dark:bg-white/10"
                        }`}
                      />
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2 mt-6"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    {mode === "login" ? "Sign In" : "Create Account"}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200 dark:border-white/5" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-3 text-slate-400 dark:text-slate-500 bg-background">
                  {mode === "login" ? "New here?" : "Already have an account?"}
                </span>
              </div>
            </div>

            <button
              onClick={() => switchMode(mode === "login" ? "register" : "login")}
              className="w-full py-2.5 rounded-xl border border-slate-200 dark:border-white/10 text-sm font-medium text-slate-600 dark:text-slate-300 hover-row transition-all"
            >
              {mode === "login" ? "Create an account" : "Sign in instead"}
            </button>
          </div>

          <p className="text-center text-xs text-slate-400 dark:text-slate-500 mt-6">
            Built with love by Ṣẹ̀kẹ̀rẹ̀ Communications
          </p>
        </div>
      </div>
    </div>
  );
}
