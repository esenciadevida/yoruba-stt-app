"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authAPI, User, UserStats } from "@/lib/api";
import { Toast } from "@/components/Toast";
import { UserCircle, Mail, Calendar, Mic, Languages, Save, Key, Loader2 } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (!token || !userData) { router.push("/auth"); return; }
    const parsed = JSON.parse(userData);
    setUser(parsed);
    setUsername(parsed.username);
    setEmail(parsed.email || "");

    authAPI.stats().then((r) => setStats(r.data)).catch(() => {});
  }, [router]);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const updated = (await authAPI.updateProfile(username, email || null)).data;
      localStorage.setItem("user", JSON.stringify(updated));
      setUser(updated);
      setToast({ message: "Profile updated successfully.", type: "success" });
    } catch (err: any) {
      setToast({ message: err.response?.data?.detail || err.message || "Failed to update profile.", type: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setChangingPassword(true);
    try {
      await authAPI.changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setToast({ message: "Password changed successfully.", type: "success" });
    } catch (err: any) {
      setToast({ message: err.response?.data?.detail || err.message || "Failed to change password.", type: "error" });
    } finally {
      setChangingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      <div className="card p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-blue-500/20">
            {user.username?.charAt(0).toUpperCase() || "U"}
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">{user.username}</h1>
            <p className="text-sm text-muted">{user.email || "No email set"}</p>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="p-4 rounded-xl border border-border text-center bg-slate-50 dark:bg-white/5">
              <div className="flex items-center justify-center gap-1.5 mb-1.5">
                <Mic className="w-4 h-4 text-blue-500" />
              </div>
              <div className="text-xl font-bold text-foreground">{stats.total_transcriptions}</div>
              <div className="text-xs text-muted mt-0.5">Transcriptions</div>
            </div>
            <div className="p-4 rounded-xl border border-border text-center bg-slate-50 dark:bg-white/5">
              <div className="flex items-center justify-center gap-1.5 mb-1.5">
                <Languages className="w-4 h-4 text-purple-500" />
              </div>
              <div className="text-xl font-bold text-foreground">{stats.total_translations}</div>
              <div className="text-xs text-muted mt-0.5">Translations</div>
            </div>
            <div className="p-4 rounded-xl border border-border text-center bg-slate-50 dark:bg-white/5">
              <div className="flex items-center justify-center gap-1.5 mb-1.5">
                <Calendar className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-sm font-bold text-foreground">
                {new Date(stats.account_created).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
              </div>
              <div className="text-xs text-muted mt-0.5">Member Since</div>
            </div>
          </div>
        )}

        <h3 className="text-sm font-medium text-foreground mb-3">Edit Profile</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              minLength={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              placeholder="optional"
            />
          </div>
          <button onClick={handleSaveProfile} disabled={saving} className="btn-primary flex items-center gap-2 text-sm">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-sm font-medium text-foreground mb-4">Change Password</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="input-field"
              placeholder="Enter current password"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="input-field"
              placeholder="Min 6 characters"
              minLength={6}
            />
          </div>
          <button
            onClick={handleChangePassword}
            disabled={changingPassword || !currentPassword || !newPassword}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {changingPassword ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
            {changingPassword ? "Updating..." : "Update Password"}
          </button>
        </div>
      </div>
    </div>
  );
}
