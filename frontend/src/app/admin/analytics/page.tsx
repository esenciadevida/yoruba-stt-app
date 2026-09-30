"use client";

import { useState, useEffect } from "react";
import { adminAPI, AdminStats, AdminUserItem } from "@/lib/api";
import { BarChart3, TrendingUp, Users, Mic, Languages, Calendar, Loader2 } from "lucide-react";

export default function AdminAnalyticsPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [topUsers, setTopUsers] = useState<AdminUserItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      adminAPI.stats().then((r) => setStats(r.data)),
      adminAPI.users(1, "").then((r) => {
        const sorted = [...r.data.items].sort((a, b) => (b.transcription_count + b.translation_count) - (a.transcription_count + a.translation_count));
        setTopUsers(sorted.slice(0, 5));
      }),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>;

  const maxCount = stats ? Math.max(...stats.daily_activity.map(d => d.count), 1) : 1;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Usage statistics and insights</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Words Transcribed", value: stats?.total_words_transcribed.toLocaleString() || "0", icon: Mic, color: "text-cyan-500" },
          { label: "Total Words Translated", value: stats?.total_words_translated.toLocaleString() || "0", icon: Languages, color: "text-purple-500" },
          { label: "Avg Words/User", value: stats && stats.total_users > 0 ? Math.round((stats.total_words_transcribed + stats.total_words_translated) / stats.total_users).toLocaleString() : "0", icon: TrendingUp, color: "text-green-500" },
          { label: "Active Rate (7d)", value: stats && stats.total_users > 0 ? `${Math.round((stats.active_users_7d / stats.total_users) * 100)}%` : "0%", icon: Users, color: "text-blue-500" },
        ].map((c) => (
          <div key={c.label} className="glass rounded-2xl p-5">
            <c.icon className={`w-5 h-5 ${c.color} mb-2`} />
            <div className="text-2xl font-bold text-foreground">{c.value}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-4 h-4 text-cyan-500" />
            <h2 className="text-sm font-semibold text-foreground">Daily Activity (7 Days)</h2>
          </div>
          {stats && (
            <div className="flex items-end gap-2 h-48">
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
          <div className="flex items-center gap-2 mb-6">
            <Users className="w-4 h-4 text-purple-500" />
            <h2 className="text-sm font-semibold text-foreground">Top Users</h2>
          </div>
          <div className="space-y-3">
            {topUsers.map((u, i) => (
              <div key={u.id} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 dark:text-slate-500 w-4">{i + 1}</span>
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white">{u.username[0].toUpperCase()}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{u.username}</p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500">{u.transcription_count} STTs · {u.translation_count} translations</p>
                </div>
                <span className="text-sm font-semibold text-foreground">{u.transcription_count + u.translation_count}</span>
              </div>
            ))}
            {topUsers.length === 0 && <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-4">No users yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
