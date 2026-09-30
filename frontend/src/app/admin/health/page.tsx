"use client";

import { useState, useEffect } from "react";
import { adminAPI, AdminSystemHealth } from "@/lib/api";
import { HeartPulse, Database, Cpu, HardDrive, Clock, RefreshCw, Loader2, CheckCircle2, XCircle } from "lucide-react";

export default function AdminHealthPage() {
  const [health, setHealth] = useState<AdminSystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    try {
      const r = await adminAPI.health();
      setHealth(r.data);
    } catch {}
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>
  );

  const formatUptime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  const items = health ? [
    { label: "System Status", value: health.status === "healthy" ? "Healthy" : "Degraded", icon: HeartPulse, ok: health.status === "healthy" },
    { label: "Database", value: health.db_connected ? "Connected" : "Disconnected", icon: Database, ok: health.db_connected },
    { label: "ASR Model", value: health.asr_model_loaded ? "Loaded" : "Not Found", icon: Cpu, ok: health.asr_model_loaded },
    { label: "Translation Engine", value: health.translation_engine, icon: Cpu, ok: true },
    { label: "Storage Used", value: `${health.total_storage_mb.toLocaleString()} MB`, icon: HardDrive, ok: true },
    { label: "Session Uptime", value: formatUptime(health.uptime_seconds), icon: Clock, ok: true },
  ] : [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">System Health</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Backend services and infrastructure status</p>
        </div>
        <button onClick={() => load(true)} disabled={refreshing} className="btn-secondary flex items-center gap-2 text-sm px-4 py-2">
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item) => (
          <div key={item.label} className="glass rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${item.ok ? "bg-green-50 dark:bg-green-950/30" : "bg-red-50 dark:bg-red-950/30"}`}>
                <item.icon className={`w-5 h-5 ${item.ok ? "text-green-500" : "text-red-500"}`} />
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
                <p className="text-sm font-semibold text-foreground">{item.value}</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              {item.ok ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500" /> : <XCircle className="w-3.5 h-3.5 text-red-500" />}
              <span className={`text-xs ${item.ok ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>{item.ok ? "Operational" : "Issue Detected"}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
