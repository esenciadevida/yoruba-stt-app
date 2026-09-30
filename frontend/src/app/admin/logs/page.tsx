"use client";

import { useState, useEffect, useCallback } from "react";
import { adminAPI, AuditLogItem } from "@/lib/api";
import { ClipboardList, Loader2, ChevronLeft, ChevronRight, Shield, UserPlus, UserMinus, Pencil, Trash2, LogIn } from "lucide-react";

const actionIcons: Record<string, { icon: typeof Shield; color: string }> = {
  create_user: { icon: UserPlus, color: "text-green-500" },
  update_user: { icon: Pencil, color: "text-blue-500" },
  delete_user: { icon: Trash2, color: "text-red-500" },
  promote_admin: { icon: Shield, color: "text-amber-500" },
  demote_admin: { icon: UserMinus, color: "text-orange-500" },
  admin_login: { icon: LogIn, color: "text-cyan-500" },
};

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const perPage = 30;

  const loadLogs = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await adminAPI.auditLogs(p);
      setLogs(res.data.items);
      setTotal(res.data.total);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { loadLogs(page); }, [page]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Audit Trail</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{total} recorded actions</p>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16 text-slate-500 dark:text-slate-400">
            <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No audit logs yet</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-white/5">
            {logs.map((log) => {
              const cfg = actionIcons[log.action] || { icon: Shield, color: "text-slate-400 dark:text-slate-500" };
              const Icon = cfg.icon;
              return (
                <div key={log.id} className="px-4 md:px-6 py-4 flex items-center gap-3 md:gap-4 hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-slate-50 dark:bg-white/5`}>
                    <Icon className={`w-4 h-4 ${cfg.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-foreground">{log.admin_username}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-slate-400">{log.action.replace("_", " ")}</span>
                    </div>
                    <p className="text-xs text-slate-400 dark:text-slate-500 truncate mt-0.5">{log.detail}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {log.ip_address && <p className="text-[10px] text-slate-400 dark:text-slate-500">{log.ip_address}</p>}
                    <p className="text-[11px] md:text-xs text-slate-400 dark:text-slate-500">{new Date(log.created_at).toLocaleString()}</p>
                  </div>
                </div>
              );
            })}
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
