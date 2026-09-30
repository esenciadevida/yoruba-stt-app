"use client";

import { useState } from "react";
import { HistoryTab } from "@/components/HistoryTab";
import { Toast } from "@/components/Toast";

export default function HistoryPage() {
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);

  return (
    <>
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}
      <HistoryTab showToast={setToast} />
    </>
  );
}
