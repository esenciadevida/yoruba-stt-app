"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { adminAPI, AdminUserDetail } from "@/lib/api";
import { Toast } from "@/components/Toast";
import { ArrowLeft, Shield, Mic, Languages, Calendar, Clock, Loader2, TrendingUp, Pencil } from "lucide-react";

export default function UserDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id;
  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);

  useEffect(() => {
    adminAPI.getUser(Number(id))
      .then((r) => setUser(r.data))
      .catch(() => setToast({ message: "Failed to load user.", type: "error" }))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>
  );

  if (!user) return (
    <div className="text-center py-20 text-slate-500 dark:text-slate-400">
      <p className="text-sm">User not found</p>
      <button onClick={() => router.push("/admin/users")} className="text-sm text-cyan-500 mt-2">Back to users</button>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      <div className="flex items-center justify-between">
        <button onClick={() => router.push("/admin/users")} className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to users
        </button>
        <button onClick={() => router.push("/admin/users")} className="btn-secondary flex items-center gap-2 text-sm px-3 py-1.5">
          <Pencil className="w-3.5 h-3.5" /> Edit User
        </button>
      </div>

      <div className="glass rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg">
            {user.username[0].toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-foreground">{user.username}</h1>
              {user.is_admin && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 text-[10px] font-semibold uppercase">
                  <Shield className="w-2.5 h-2.5" /> Admin
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{user.email || "No email"}</p>
            <div className="flex items-center gap-4 mt-1 text-xs text-slate-400 dark:text-slate-500">
              <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Joined {new Date(user.created_at).toLocaleDateString()}</span>
              {user.last_active && <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Last active {new Date(user.last_active).toLocaleDateString()}</span>}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-cyan-50 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-500/10 text-center">
            <Mic className="w-5 h-5 text-cyan-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-foreground">{user.transcription_count}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Transcriptions</div>
          </div>
          <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-500/10 text-center">
            <Languages className="w-5 h-5 text-purple-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-foreground">{user.translation_count}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Translations</div>
          </div>
          <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-500/10 text-center">
            <TrendingUp className="w-5 h-5 text-blue-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-foreground">{user.total_words_transcribed.toLocaleString()}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Words Transcribed</div>
          </div>
          <div className="p-4 rounded-xl bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-500/10 text-center">
            <TrendingUp className="w-5 h-5 text-green-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-foreground">{user.total_words_translated.toLocaleString()}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Words Translated</div>
          </div>
        </div>
      </div>

      <div className="glass rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-foreground mb-4">Recent Activity</h2>
        {user.recent_activity.length === 0 ? (
          <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-8">No activity yet</p>
        ) : (
          <div className="space-y-3">
            {user.recent_activity.map((a) => (
              <div key={a.id} className="flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${a.activity_type === "transcription" ? "bg-cyan-50 dark:bg-cyan-950/30" : "bg-purple-50 dark:bg-purple-950/30"}`}>
                  {a.activity_type === "transcription"
                    ? <Mic className="w-3.5 h-3.5 text-cyan-500" />
                    : <Languages className="w-3.5 h-3.5 text-purple-500" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground leading-relaxed">{a.summary}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase ${a.activity_type === "transcription" ? "bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400" : "bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400"}`}>{a.activity_type}</span>
                    {a.engine && <span className="text-[10px] text-slate-400 dark:text-slate-500">{a.engine}</span>}
                  </div>
                </div>
                <span className="text-[11px] text-slate-400 dark:text-slate-500 flex-shrink-0">{new Date(a.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
