"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Smartphone } from "lucide-react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export function usePwaInstall() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [installing, setInstalling] = useState(false);
  const promptRef = useRef<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      promptRef.current = e as BeforeInstallPromptEvent;
      setInstallPrompt(promptRef.current);
    };
    const handleInstalled = () => {
      setIsInstalled(true);
      setInstallPrompt(null);
      promptRef.current = null;
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    window.addEventListener("appinstalled", handleInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);

  const canInstall = installPrompt !== null && !isInstalled;

  const promptInstall = useCallback(async () => {
    const prompt = promptRef.current;
    if (!prompt) return;
    setInstalling(true);
    try {
      await prompt.prompt();
      const choice = await prompt.userChoice;
      if (choice.outcome === "accepted") {
        setIsInstalled(true);
        setInstallPrompt(null);
        promptRef.current = null;
      }
    } finally {
      setInstalling(false);
    }
  }, []);

  return { canInstall, isInstalled, installing, promptInstall };
}

export function InstallPWAButton({ compact = false }: { compact?: boolean }) {
  const { canInstall, isInstalled, installing, promptInstall } = usePwaInstall();

  if (!canInstall) return null;

  return (
    <button
      onClick={promptInstall}
      disabled={installing}
      className={
        compact
          ? "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 transition-colors disabled:opacity-50"
          : "btn-primary flex items-center gap-2 text-sm"
      }
      title={
        isInstalled ? "App is installed" : "Install Bámi-Sọ̀rọ̀ as an app for faster access"
      }
    >
      <Smartphone className="w-3.5 h-3.5" />
      {installing ? "Installing..." : "Install App"}
    </button>
  );
}

export function InstallPWABanner() {
  const { canInstall, isInstalled, installing, promptInstall } = usePwaInstall();
  const [dismissed, setDismissed] = useState(false);

  if (!canInstall || dismissed) return null;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] w-[calc(100%-2rem)] max-w-md px-4 py-3 bg-card border border-border rounded-2xl shadow-lg animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 text-white shrink-0">
          <Smartphone className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground">Install Bámi-Sọ̀rọ̀</p>
          <p className="text-xs text-muted">Get offline access & a home-screen icon</p>
        </div>
        <button
          onClick={promptInstall}
          disabled={installing}
          className="btn-primary text-xs px-3 py-2"
        >
          {installing ? "Installing..." : "Install"}
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="p-1.5 text-muted hover:text-foreground transition-colors"
          aria-label="Dismiss install prompt"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}