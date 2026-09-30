"use client";

import { useState, useEffect } from "react";
import { adminAPI, AdminSystemHealth } from "@/lib/api";
import { Settings, Database, Cpu, Shield, Globe, Loader2 } from "lucide-react";

export default function AdminSettingsPage() {
  const [health, setHealth] = useState<AdminSystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.health().then((r) => setHealth(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>;

  const sections = [
    {
      title: "Authentication",
      icon: Shield,
      items: [
        { label: "JWT Secret", value: "••••••••••••••••" },
        { label: "Token Expiry", value: "24 hours" },
        { label: "Password Hashing", value: "bcrypt" },
      ],
    },
    {
      title: "Database",
      icon: Database,
      items: [
        { label: "Engine", value: "MySQL 8.0" },
        { label: "Connection", value: health?.db_connected ? "Connected" : "Disconnected" },
        { label: "Database", value: "bami_soro" },
      ],
    },
    {
      title: "ASR Engines (cascade)",
      icon: Cpu,
      items: [
        { label: "Primary", value: "gpt-4o-transcribe (OpenAI)" },
        { label: "Fallback 1", value: "whisper-1 (OpenAI)" },
        { label: "Fallback 2", value: "W2V-BERT Yoruba (local)" },
        { label: "Fallback 3", value: "Whisper Yoruba (local)" },
        { label: "Backend", value: "Transformers (PyTorch)" },
      ],
    },
    {
      title: "Translation",
      icon: Globe,
      items: [
        { label: "Code-switch", value: "GPT-4o-mini (OpenAI)" },
        { label: "EN → YO", value: "NLLB-200 + GPT-4o-mini" },
        { label: "YO → EN", value: "GPT-4o-mini + Opus-MT" },
        { label: "Model Path", value: "models/nllb-200-distilled-600M/" },
      ],
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">System Settings</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Backend configuration and system information</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sections.map((section) => (
          <div key={section.title} className="glass rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <section.icon className="w-4 h-4 text-white" />
              </div>
              <h2 className="text-sm font-semibold text-foreground">{section.title}</h2>
            </div>
            <div className="space-y-3">
              {section.items.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 dark:text-slate-400">{item.label}</span>
                  <span className="text-xs font-medium text-foreground">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
