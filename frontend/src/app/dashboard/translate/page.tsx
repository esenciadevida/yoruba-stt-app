"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { TranslateTab } from "@/components/TranslateTab";
import { Toast } from "@/components/Toast";

export default function TranslatePage() {
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);
  const searchParams = useSearchParams();
  const prefilledText = searchParams.get("text") || "";

  return (
    <>
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}
      <TranslateTab showToast={setToast} prefilledText={prefilledText} />
    </>
  );
}
