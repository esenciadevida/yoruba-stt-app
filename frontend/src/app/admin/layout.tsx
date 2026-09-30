"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeToggle";
import { InstallPWAButton } from "@/components/InstallPWA";
import { LayoutDashboard, Users, Activity, HeartPulse, Shield, Settings, ClipboardList, BarChart3, LogOut, UserCircle, Menu, X } from "lucide-react";

const nav = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/admin" },
  { label: "Users", icon: Users, href: "/admin/users" },
  { label: "Activity", icon: Activity, href: "/admin/activity" },
  { label: "Analytics", icon: BarChart3, href: "/admin/analytics" },
  { label: "Audit Logs", icon: ClipboardList, href: "/admin/logs" },
  { label: "Health", icon: HeartPulse, href: "/admin/health" },
  { label: "Settings", icon: Settings, href: "/admin/settings" },
  { label: "Profile", icon: UserCircle, href: "/admin/profile" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [adminUser, setAdminUser] = useState<{ username: string; is_admin: boolean } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (pathname === "/admin/login") return;
    const token = localStorage.getItem("admin_token");
    const userData = localStorage.getItem("admin_user");
    if (!token || !userData) { router.push("/admin/login"); return; }
    try {
      const parsed = JSON.parse(userData);
      if (!parsed.is_admin) { router.push("/admin/login"); return; }
      setAdminUser(parsed);
    } catch { router.push("/admin/login"); }
  }, [router, pathname]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  const logout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");
    router.push("/admin/login");
  };

  if (pathname === "/admin/login") return <>{children}</>;

  if (!adminUser) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const sidebarContent = (
    <>
      <div className="p-4 border-b border-slate-200 dark:border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-sm font-bold gradient-text">Bámi-Sọ̀rọ̀</span>
            <div className="text-[10px] text-amber-600 dark:text-amber-400 font-semibold uppercase tracking-wider">Admin Portal</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {nav.map(({ label, icon: Icon, href }) => (
          <button
            key={href}
            onClick={() => router.push(href)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
              pathname === href
                ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/20"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5"
            }`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </button>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-200 dark:border-white/5 space-y-2">
        <div className="flex items-center gap-2 px-3 py-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-xs font-bold text-white">
            {adminUser.username[0].toUpperCase()}
          </div>
          <span className="text-xs font-medium text-slate-600 dark:text-slate-300 truncate">{adminUser.username}</span>
        </div>
        <div className="flex items-center justify-between px-3">
          <InstallPWAButton compact />
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button onClick={logout} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 dark:text-slate-500 hover:text-red-500 transition-colors" title="Sign out" aria-label="Sign out">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-background flex">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 border-r border-slate-200 dark:border-white/5 flex-col shrink-0 safe-top">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <aside className="fixed inset-y-0 left-0 z-50 w-72 flex flex-col bg-background border-r safe-top">
            <div className="flex justify-end p-3 pb-0">
              <button
                onClick={() => setSidebarOpen(false)}
                className="rounded-lg p-2 text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-700 dark:hover:text-white transition-colors"
                aria-label="Close menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            {sidebarContent}
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Top Bar */}
        <header className="flex md:hidden h-14 items-center justify-between px-3 border-b border-slate-200 dark:border-white/5 bg-background backdrop-blur-lg sticky top-0 z-40 gap-2 safe-top">
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-700 dark:hover:text-white transition-colors"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shrink-0">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-bold gradient-text truncate">Admin</span>
          </div>
          <div className="flex items-center gap-0.5 shrink-0">
            <InstallPWAButton compact />
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8">{children}</main>

        {/* iOS safe-area spacer */}
        <div className="h-[env(safe-area-inset-bottom)] md:hidden" />
      </div>
    </div>
  );
}