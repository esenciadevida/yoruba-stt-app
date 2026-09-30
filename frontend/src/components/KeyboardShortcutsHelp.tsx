"use client";

import { useState } from "react";
import { Keyboard, X } from "lucide-react";

const shortcuts = [
  { keys: "Ctrl + Enter", action: "Transcribe audio" },
  { keys: "Ctrl + Shift + T", action: "Translate text" },
  { keys: "Ctrl + Shift + C", action: "Copy result" },
  { keys: "Ctrl + N", action: "New recording" },
  { keys: "Ctrl + D", action: "Toggle dark mode" },
];

export function KeyboardShortcutsHelp() {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white transition-all"
        title="Keyboard shortcuts"
      >
        <Keyboard className="w-4 h-4" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-card border border-border rounded-xl shadow-lg p-4 z-50 animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">Keyboard Shortcuts</h3>
            <button onClick={() => setOpen(false)} className="text-muted hover:text-foreground">
              <X size={14} />
            </button>
          </div>
          <div className="space-y-2">
            {shortcuts.map((s) => (
              <div key={s.keys} className="flex items-center justify-between text-xs">
                <span className="text-muted">{s.action}</span>
                <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded text-[10px] font-mono text-foreground">
                  {s.keys}
                </kbd>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
