"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Mic,
  Languages,
  Clock,
  User,
  LogOut,
  Menu,
  X,
  AudioWaveform,
} from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { KeyboardShortcutsHelp } from "@/components/KeyboardShortcutsHelp";
import { InstallPWAButton } from "@/components/InstallPWA";
import { isTokenExpired } from "@/lib/api";

const navItems = [
  { icon: Mic, label: "Speech Recognition", href: "/dashboard" },
  { icon: Languages, label: "Translate", href: "/dashboard/translate" },
  { icon: Clock, label: "History", href: "/dashboard/history" },
  { icon: User, label: "Profile", href: "/dashboard/profile" },
];

const pageTitles: Record<string, string> = {
  "/dashboard": "Speech Recognition",
  "/dashboard/translate": "Translate",
  "/dashboard/history": "History",
  "/dashboard/profile": "Profile",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<{ username?: string } | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token || isTokenExpired(token)) {
      router.push("/auth");
      return;
    }

    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        setUser(null);
      }
    }
  }, [router]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/auth");
  };

  const pageTitle = pageTitles[pathname] || "Dashboard";

  const sidebarContent = (
    <>
      <div className="flex h-16 items-center gap-3 px-5 border-b border-border">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/20">
          <AudioWaveform className="h-5 w-5" />
        </div>
        <div>
          <span className="text-base font-bold tracking-tight text-foreground">Bami-Soro</span>
          <p className="text-[10px] text-muted -mt-0.5">Yoruba STT</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {navItems.map((item) => {
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-muted hover-row hover:text-foreground"
              }`}
            >
              <item.icon className={`h-[18px] w-[18px] shrink-0 ${isActive ? "text-blue-600 dark:text-blue-400" : ""}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted transition-all hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400"
        >
          <LogOut className="h-[18px] w-[18px] shrink-0" />
          Logout
        </button>
      </div>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card">
        {sidebarContent}
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-card border-r border-border animate-in slide-in-from-left duration-200 safe-top">
            <div className="flex h-16 items-center justify-between px-5 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/20">
                  <AudioWaveform className="h-5 w-5" />
                </div>
                <span className="text-base font-bold tracking-tight">
                  Bami-Soro
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="rounded-lg p-1.5 text-muted hover:text-foreground hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <nav className="flex-1 space-y-0.5 px-3 py-4">
              {navItems.map((item) => {
                const isActive =
                  item.href === "/dashboard"
                    ? pathname === "/dashboard"
                    : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                      isActive
                        ? "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400"
                        : "text-muted hover-row hover:text-foreground"
                    }`}
                  >
                    <item.icon className="h-[18px] w-[18px] shrink-0" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="border-t border-border p-3">
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted transition-all hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400"
              >
                <LogOut className="h-[18px] w-[18px] shrink-0" />
                Logout
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-border bg-card backdrop-blur-lg px-4 md:px-6 safe-top">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-1.5 text-muted hover:text-foreground hover:bg-slate-100 dark:hover:bg-white/5 md:hidden transition-colors"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-sm md:hidden shrink-0">
              <AudioWaveform className="h-4 w-4" />
            </div>
            <h1 className="text-lg font-semibold text-foreground truncate">{pageTitle}</h1>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <InstallPWAButton compact />
            <KeyboardShortcutsHelp />
            <ThemeToggle />
            {user && (
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white text-sm font-semibold shadow-sm">
                  {user.username?.charAt(0).toUpperCase() || "U"}
                </div>
                <span className="hidden text-sm font-medium md:inline text-foreground">
                  {user.username || "User"}
                </span>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
