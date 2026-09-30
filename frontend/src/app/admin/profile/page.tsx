"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authAPI, User } from "@/lib/api";
import { Toast } from "@/components/Toast";
import { UserCircle, Mail, Shield, Calendar, Save, Key, Loader2, ArrowLeft } from "lucide-react";

export default function AdminProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem("admin_user");
    const token = localStorage.getItem("admin_token");
    if (!token || !userData) { router.push("/admin/login"); return; }
    const parsed = JSON.parse(userData);
    setUser(parsed);
    setUsername(parsed.username);
    setEmail(parsed.email || "");
  }, [router]);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem("admin_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ username, email: email || null }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to update profile");
      }
      const updated = await res.json();
      localStorage.setItem("admin_user", JSON.stringify({ ...user, ...updated }));
      setUser({ ...user!, ...updated });
      setToast({ message: "Profile updated successfully.", type: "success" });
    } catch (err: any) {
      setToast({ message: err.message || "Failed to update profile.", type: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setChangingPassword(true);
    try {
      const token = localStorage.getItem("admin_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/password`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to change password");
      }
      setCurrentPassword("");
      setNewPassword("");
      setToast({ message: "Password changed successfully.", type: "success" });
    } catch (err: any) {
      setToast({ message: err.message || "Failed to change password.", type: "error" });
    } finally {
      setChangingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      <div className="glass rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg shadow-amber-500/20">
            {user.username[0].toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-foreground">{user.username}</h1>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 text-[10px] font-semibold uppercase">
                <Shield className="w-2.5 h-2.5" /> Admin
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{user.email || "No email set"}</p>
            <p className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1 mt-1">
              <Calendar className="w-3 h-3" /> Joined {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <UserCircle className="w-4 h-4 text-slate-400 dark:text-slate-500" /> Edit Profile
        </h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="input-field" minLength={3} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="optional" />
          </div>
          <button onClick={handleSaveProfile} disabled={saving} className="btn-primary flex items-center gap-2 text-sm">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      <div className="glass rounded-2xl p-8">
        <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
          <Key className="w-4 h-4 text-slate-400 dark:text-slate-500" /> Change Password
        </h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Current Password</label>
            <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="input-field" placeholder="Enter current password" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">New Password</label>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="input-field" minLength={6} placeholder="Min 6 characters" />
          </div>
          <button onClick={handleChangePassword} disabled={changingPassword || !currentPassword || !newPassword} className="btn-primary flex items-center gap-2 text-sm">
            {changingPassword ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
            {changingPassword ? "Updating..." : "Update Password"}
          </button>
        </div>
      </div>
    </div>
  );
}
