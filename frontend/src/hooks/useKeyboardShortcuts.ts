"use client";

import { useEffect } from "react";

interface ShortcutHandlers {
  onTranscribe?: () => void;
  onTranslate?: () => void;
  onCopy?: () => void;
  onNewRecording?: () => void;
  onToggleTheme?: () => void;
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isCtrl = e.ctrlKey || e.metaKey;

      // Ctrl+Enter: Transcribe
      if (isCtrl && e.key === "Enter") {
        e.preventDefault();
        handlers.onTranscribe?.();
      }

      // Ctrl+Shift+T: Translate
      if (isCtrl && e.shiftKey && e.key === "T") {
        e.preventDefault();
        handlers.onTranslate?.();
      }

      // Ctrl+Shift+C: Copy
      if (isCtrl && e.shiftKey && e.key === "C") {
        e.preventDefault();
        handlers.onCopy?.();
      }

      // Ctrl+N: New recording
      if (isCtrl && e.key === "n") {
        e.preventDefault();
        handlers.onNewRecording?.();
      }

      // Ctrl+D: Toggle theme
      if (isCtrl && e.key === "d") {
        e.preventDefault();
        handlers.onToggleTheme?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlers]);
}
