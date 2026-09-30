"use client";

import { useState, useEffect, useCallback } from "react";
import { adminAPI, AdminActivityItem } from "@/lib/api";
import { Activity, Mic, Languages, Loader2, ChevronLeft, ChevronRight, Filter } from "lucide-react";

export default function AdminActivityPage() {
  const [items, setItems] = useState<AdminActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const perPage = 30;

  const loadActivity = useCallback(async (p: number, type: string) => {
    setLoading(true);
    try {
      const res = await adminAPI.activity(p, type || undefined);
      setItems(res.data.items);
      setTotal(res.data.total);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { setPage(1); }, [typeFilter]);
  useEffect(() => { loadActivity(page, typeFilter); }, [page, typeFilter, loadActivity]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Activity Feed</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{total} total activities</p>
        </div>
        <div className="flex gap-1 p-1 rounded-lg bg-slate-100 dark:bg-white/5">
          {[{ value: "", label: "All" }, { value: "transcription", label: "STT" }, { value: "translation", label: "Translation" }].map(({ value, label }) => (
            <button key={value} onClick={() => setTypeFilter(value)} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${typeFilter === value ? "bg-white dark:bg-white/10 text-foreground shadow-sm" : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white"}`}>{label}</button>
          ))}
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-slate-500 dark:text-slate-400"><Activity className="w-12 h-12 mx-auto mb-3 opacity-20" /><p className="text-sm">No activity yet</p></div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-white/5">
            {items.map((a) => (
              <div key={a.id} className="px-4 md:px-6 py-4 flex items-center gap-3 md:gap-4 hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${a.activity_type === "transcription" ? "bg-cyan-50 dark:bg-cyan-950/30" : "bg-purple-50 dark:bg-purple-950/30"}`}>
                  {a.activity_type === "transcription"
                    ? <Mic className="w-4 h-4 text-cyan-500" />
                    : <Languages className="w-4 h-4 text-purple-500" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-foreground">{a.user}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase ${a.activity_type === "transcription" ? "bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400" : "bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400"}`}>{a.activity_type}</span>
                    {a.engine && <span className="text-[10px] text-slate-400 dark:text-slate-500">{a.engine}</span>}
                  </div>
                  <p className="text-xs text-slate-400 dark:text-slate-500 truncate mt-0.5">{a.summary}</p>
                </div>
                <span className="text-[11px] md:text-xs text-slate-400 dark:text-slate-500 whitespace-nowrap shrink-0">{new Date(a.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 dark:border-white/5">
            <span className="text-xs text-slate-400 dark:text-slate-500">Page {page} of {totalPages}</span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500 disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
              <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500 disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
