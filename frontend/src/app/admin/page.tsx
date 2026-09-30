"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { adminAPI, AdminStats, AdminActivityItem } from "@/lib/api";
import { Users, Mic, Languages, UserCheck, UserPlus, Loader2, Activity, TrendingUp, BarChart3 } from "lucide-react";

export default function AdminOverview() {
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<AdminActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      adminAPI.stats().then((r) => setStats(r.data)),
      adminAPI.activity(1).then((r) => setRecentActivity(r.data.items.slice(0, 5))),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex justify-center py-20">
      <Loader2 className="w-6 h-6 animate-spin text-cyan-500" />
    </div>
  );

  const cards = stats ? [
    { label: "Total Users", value: stats.total_users, icon: Users, color: "from-blue-500 to-indigo-600", shadow: "shadow-blue-500/20" },
    { label: "Transcriptions", value: stats.total_transcriptions, icon: Mic, color: "from-cyan-500 to-blue-600", shadow: "shadow-cyan-500/20" },
    { label: "Translations", value: stats.total_translations, icon: Languages, color: "from-purple-500 to-pink-600", shadow: "shadow-purple-500/20" },
    { label: "Active (7d)", value: stats.active_users_7d, icon: UserCheck, color: "from-green-500 to-emerald-600", shadow: "shadow-green-500/20" },
    { label: "New Signups (7d)", value: stats.recent_signups, icon: UserPlus, color: "from-amber-500 to-orange-600", shadow: "shadow-amber-500/20" },
    { label: "Words Translated", value: stats.total_words_translated, icon: TrendingUp, color: "from-rose-500 to-pink-600", shadow: "shadow-rose-500/20" },
  ] : [];

  const maxCount = stats ? Math.max(...stats.daily_activity.map(d => d.count), 1) : 1;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Admin Dashboard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Platform overview and management</p>
        </div>
        <button
          onClick={() => router.push("/admin/users")}
          className="btn-primary flex items-center gap-2 text-sm px-4 py-2"
        >
          <Users className="w-4 h-4" /> Manage Users
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="glass rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} ${card.shadow} flex items-center justify-center shadow-lg`}>
                <card.icon className="w-4 h-4 text-white" />
              </div>
            </div>
            <div className="text-2xl font-bold text-foreground">{card.value.toLocaleString()}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{card.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-4 h-4 text-cyan-500" />
            <h2 className="text-sm font-semibold text-foreground">Activity (Last 7 Days)</h2>
          </div>
          {stats && (
            <div className="flex items-end gap-2 h-40">
              {stats.daily_activity.map((day, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-[10px] text-slate-400 dark:text-slate-500">{day.count}</span>
                  <div className="w-full rounded-t-md bg-gradient-to-t from-cyan-500 to-blue-500 transition-all" style={{ height: `${(day.count / maxCount) * 100}%`, minHeight: day.count > 0 ? "4px" : "2px", opacity: day.count > 0 ? 1 : 0.2 }} />
                  <span className="text-[10px] text-slate-400 dark:text-slate-500">{day.date}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-500" />
              <h2 className="text-sm font-semibold text-foreground">Recent Activity</h2>
            </div>
            <button onClick={() => router.push("/admin/activity")} className="text-xs text-cyan-500 hover:text-cyan-600 dark:hover:text-cyan-400">View all</button>
          </div>
          <div className="space-y-3">
            {recentActivity.map((a) => (
              <div key={a.id} className="flex items-start gap-3">
                <div className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 mt-0.5 ${a.activity_type === "transcription" ? "bg-cyan-50 dark:bg-cyan-950/30" : "bg-purple-50 dark:bg-purple-950/30"}`}>
                  {a.activity_type === "transcription"
                    ? <Mic className="w-3 h-3 text-cyan-500" />
                    : <Languages className="w-3 h-3 text-purple-500" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground">{a.user}</p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate">{a.summary}</p>
                </div>
                <span className="text-[10px] text-slate-400 dark:text-slate-500 flex-shrink-0">{new Date(a.created_at).toLocaleDateString()}</span>
              </div>
            ))}
            {recentActivity.length === 0 && (
              <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-4">No activity yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
