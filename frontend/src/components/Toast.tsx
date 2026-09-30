"use client";

import { useEffect } from "react";
import { AlertCircle, Check, X } from "lucide-react";

interface ToastProps {
  message: string;
  type: "error" | "success";
  onDismiss: () => void;
}

export function Toast({ message, type, onDismiss }: ToastProps) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div
      className={`fixed top-4 right-4 z-[100] max-w-sm animate-fade-in rounded-xl px-4 py-3 flex items-center gap-3 backdrop-blur-xl shadow-2xl border ${
        type === "error"
          ? "bg-red-50 dark:bg-red-950/50 border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-300"
          : "bg-green-50 dark:bg-green-950/50 border-green-200 dark:border-green-500/20 text-green-600 dark:text-green-300"
      }`}
    >
      {type === "error" ? (
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
      ) : (
        <Check className="w-5 h-5 flex-shrink-0" />
      )}
      <span className="text-sm flex-1">{message}</span>
      <button onClick={onDismiss} className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-white transition-colors">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
