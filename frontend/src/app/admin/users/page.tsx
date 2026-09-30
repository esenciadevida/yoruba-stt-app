"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { adminAPI, AdminUserItem } from "@/lib/api";
import { Toast } from "@/components/Toast";
import { Users, Search, Shield, ShieldOff, Trash2, Loader2, ChevronLeft, ChevronRight, Mic, Languages, UserPlus, X, Pencil, Eye, Clock } from "lucide-react";

export default function AdminUsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editUser, setEditUser] = useState<AdminUserItem | null>(null);

  const loadUsers = useCallback(async (p: number, q: string, role: string) => {
    setLoading(true);
    try {
      const res = await adminAPI.users(p, q, role || undefined);
      setUsers(res.data.items);
      setTotal(res.data.total);
    } catch {
      setToast({ message: "Failed to load users.", type: "error" });
    }
    setLoading(false);
  }, []);

  useEffect(() => { setPage(1); }, [search, roleFilter]);
  useEffect(() => { loadUsers(page, search, roleFilter); }, [page, search, roleFilter, loadUsers]);

  const toggleRole = async (id: number) => {
    try {
      const res = await adminAPI.toggleRole(id);
      setUsers((prev) => prev.map((u) => u.id === id ? { ...u, is_admin: res.data.is_admin } : u));
      setToast({ message: `User ${res.data.is_admin ? "promoted to admin" : "removed from admin"}.`, type: "success" });
    } catch {
      setToast({ message: "Failed to update role.", type: "error" });
    }
  };

  const deleteUser = async (id: number) => {
    try {
      await adminAPI.deleteUser(id);
      setDeleteConfirm(null);
      loadUsers(page, search, roleFilter);
      setToast({ message: "User deleted.", type: "success" });
    } catch {
      setToast({ message: "Failed to delete user.", type: "error" });
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}
      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); loadUsers(1, search, roleFilter); }} onError={(m) => setToast({ message: m, type: "error" })} />}
      {editUser && <EditUserModal user={editUser} onClose={() => setEditUser(null)} onUpdated={() => { setEditUser(null); loadUsers(page, search, roleFilter); }} onError={(m) => setToast({ message: m, type: "error" })} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">User Management</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{total} registered users</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm px-4 py-2">
          <UserPlus className="w-4 h-4" /> Create User
        </button>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search users..." className="input-field pl-10" />
        </div>
        <div className="flex gap-1 p-1 rounded-lg bg-slate-100 dark:bg-white/5">
          {[{ value: "", label: "All" }, { value: "user", label: "Users" }, { value: "admin", label: "Admins" }].map(({ value, label }) => (
            <button key={value} onClick={() => setRoleFilter(value)} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${roleFilter === value ? "bg-white dark:bg-white/10 text-foreground shadow-sm" : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white"}`}>{label}</button>
          ))}
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-cyan-500" /></div>
        ) : users.length === 0 ? (
          <div className="text-center py-16 text-slate-500 dark:text-slate-400"><Users className="w-12 h-12 mx-auto mb-3 opacity-20" /><p className="text-sm">No users found</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-white/5">
                  <th className="text-left text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">User</th>
                  <th className="text-left text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">Email</th>
                  <th className="text-center text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">Role</th>
                  <th className="text-center text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">STT</th>
                  <th className="text-center text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">Translate</th>
                  <th className="text-right text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">Joined</th>
                  <th className="text-right text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white">{u.username[0].toUpperCase()}</div>
                        <span className="text-sm font-medium text-foreground">{u.username}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">{u.email || "—"}</td>
                    <td className="px-6 py-4 text-center">
                      {u.is_admin ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 text-[10px] font-semibold uppercase"><Shield className="w-2.5 h-2.5" /> Admin</span>
                      ) : <span className="text-xs text-slate-400 dark:text-slate-500">User</span>}
                    </td>
                    <td className="px-6 py-4 text-center"><span className="inline-flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400"><Mic className="w-3 h-3 text-cyan-400" /> {u.transcription_count}</span></td>
                    <td className="px-6 py-4 text-center"><span className="inline-flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400"><Languages className="w-3 h-3 text-purple-400" /> {u.translation_count}</span></td>
                    <td className="px-6 py-4 text-right text-xs text-slate-400 dark:text-slate-500">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right">
                      {deleteConfirm === u.id ? (
                        <div className="flex items-center gap-1 justify-end">
                          <button onClick={() => deleteUser(u.id)} className="px-2 py-1 rounded-md bg-red-500 text-white text-xs font-medium hover:bg-red-600">Delete</button>
                          <button onClick={() => setDeleteConfirm(null)} className="px-2 py-1 rounded-md bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-slate-300 text-xs">Cancel</button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 justify-end">
                          <button onClick={() => router.push(`/admin/users/${u.id}`)} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500 hover:text-cyan-500 transition-colors" title="View details"><Eye className="w-4 h-4" /></button>
                          <button onClick={() => setEditUser(u)} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500 hover:text-blue-500 transition-colors" title="Edit user"><Pencil className="w-4 h-4" /></button>
                          <button onClick={() => toggleRole(u.id)} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500 hover:text-amber-500 transition-colors" title={u.is_admin ? "Remove admin" : "Make admin"}>
                            {u.is_admin ? <ShieldOff className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                          </button>
                          <button onClick={() => setDeleteConfirm(u.id)} className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/50 text-slate-400 dark:text-slate-500 hover:text-red-500 transition-colors" title="Delete user"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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

function CreateUserModal({ onClose, onCreated, onError }: { onClose: () => void; onCreated: () => void; onError: (msg: string) => void }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await adminAPI.createUser({ username, password, email: email || undefined, is_admin: isAdmin });
      onCreated();
    } catch (err: any) {
      onError(err.response?.data?.detail || "Failed to create user");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="glass rounded-2xl p-6 w-full max-w-md animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-foreground">Create User</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="input-field" required minLength={3} autoFocus />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Email (optional)</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="user@example.com" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" required minLength={6} placeholder="Min 6 characters" />
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={isAdmin} onChange={(e) => setIsAdmin(e.target.checked)} className="w-4 h-4 rounded border-slate-300 dark:border-zinc-700 text-cyan-500 focus:ring-cyan-500" />
            <span className="text-sm text-slate-600 dark:text-slate-300">Grant admin privileges</span>
          </label>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading || !username || !password} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
              {loading ? "Creating..." : "Create User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditUserModal({ user, onClose, onUpdated, onError }: { user: AdminUserItem; onClose: () => void; onUpdated: () => void; onError: (msg: string) => void }) {
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email || "");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await adminAPI.updateUser(user.id, {
        username,
        email: email || undefined,
        password: password || undefined,
      });
      onUpdated();
    } catch (err: any) {
      onError(err.response?.data?.detail || "Failed to update user");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="glass rounded-2xl p-6 w-full max-w-md animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-foreground">Edit User</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="input-field" required minLength={3} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="optional" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">New Password (leave blank to keep current)</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" minLength={6} placeholder="Min 6 characters" />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading || !username} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pencil className="w-4 h-4" />}
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
