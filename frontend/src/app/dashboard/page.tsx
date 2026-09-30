"use client";

import { useState, useEffect } from "react";
import { STTTab } from "@/components/STTTab";
import { Toast } from "@/components/Toast";
import { OnboardingCard } from "@/components/OnboardingCard";

const ONBOARDING_KEY = "bami-soro-onboarded-v1";

export default function DashboardPage() {
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);
  // Read localStorage only after hydration (useEffect) so the server-rendered
  // HTML matches the client's first render. Reading it in the useState
  // initializer makes the client show the card while the server does not,
  // which breaks React hydration.
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
    try {
      if (localStorage.getItem(ONBOARDING_KEY) !== "1") setShowOnboarding(true);
    } catch {
      // localStorage unavailable (private mode etc.) — skip onboarding.
    }
  }, []);

  const dismissOnboarding = () => {
    localStorage.setItem(ONBOARDING_KEY, "1");
    setShowOnboarding(false);
  };

  return (
    <>
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}
      <div className="max-w-2xl mx-auto space-y-5">
        {hydrated && showOnboarding && <OnboardingCard onDismiss={dismissOnboarding} />}
        <STTTab showToast={setToast} />
      </div>
    </>
  );
}