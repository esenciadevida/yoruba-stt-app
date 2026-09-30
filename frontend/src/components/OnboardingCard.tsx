"use client";

import { useState } from "react";
import { Mic, Languages, History, X, Sparkles, ChevronRight } from "lucide-react";

interface OnboardingCardProps {
  onDismiss: () => void;
}

const STEPS = [
  {
    icon: Mic,
    color: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10",
    title: "Tap to record",
    body: "Speak Yorùbá or English. The app automatically detects the language and switches between them mid-sentence.",
  },
  {
    icon: Sparkles,
    color: "text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10",
    title: "Get a polished transcript",
    body: "Automatic tone marks, correct spelling of ẹ·ọ·ṣ subdot letters, and confidence highlighting so you know what to double-check.",
  },
  {
    icon: History,
    color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10",
    title: "Replay, pin & redo",
    body: "Every transcription keeps its audio in History — replay it, pin it to the top, rename it, or re-run it with a different engine.",
  },
];

export function OnboardingCard({ onDismiss }: OnboardingCardProps) {
  const [step, setStep] = useState(0);
  const current = STEPS[step];

  const next = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      onDismiss();
    }
  };

  const Icon = current.icon;

  return (
    <div className="card p-5 relative animate-fade-in overflow-hidden">
      <button
        onClick={onDismiss}
        className="absolute top-3 right-3 p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
        aria-label="Dismiss onboarding"
      >
        <X size={15} />
      </button>

      <div className="flex items-start gap-4">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${current.color}`}>
          <Icon size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-foreground">{current.title}</p>
          <p className="text-xs text-secondary mt-1 leading-relaxed">{current.body}</p>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-1.5">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`h-1.5 rounded-full transition-all ${
                i === step
                  ? "w-6 bg-blue-600 dark:bg-blue-400"
                  : "w-1.5 bg-slate-200 dark:bg-white/15"
              }`}
            />
          ))}
        </div>
        <button
          onClick={next}
          className="flex items-center gap-1 text-xs font-medium text-blue-600 dark:text-blue-400 hover:gap-2 transition-all"
        >
          {step < STEPS.length - 1 ? (
            <>
              Next
              <ChevronRight size={14} />
            </>
          ) : (
            <>
              <Sparkles size={13} />
              Get started
            </>
          )}
        </button>
      </div>
    </div>
  );
}