"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { translateAPI, TranslateResult } from "@/lib/api";
import { Languages, Copy, Check, Download, ArrowRight, Loader2, Shield, Sparkles, X } from "lucide-react";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { useTheme } from "next-themes";

type Direction = "auto";

interface TranslateTabProps {
  showToast: (t: { message: string; type: "error" | "success" }) => void;
  prefilledText?: string;
}

export function TranslateTab({ showToast, prefilledText }: TranslateTabProps) {
  const [input, setInput] = useState(prefilledText || "");
  const direction: Direction = "auto";
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TranslateResult | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedSource, setCopiedSource] = useState(false);
  const [copiedTranslation, setCopiedTranslation] = useState(false);
  const streamRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [streamingText]);

  const MAX_CHARS = 2000;

  const handleTranslate = async () => {
    if (!input.trim()) {
      showToast({ message: "Please enter text to translate.", type: "error" });
      return;
    }

    if (input.length > MAX_CHARS) {
      showToast({ message: `Text too long (${input.length}/${MAX_CHARS} chars). Try shorter text.`, type: "error" });
      return;
    }

    setLoading(true);
    setIsStreaming(true);
    setStreamingText("");
    setResult(null);

    abortRef.current = new AbortController();

    translateAPI.translateStream(
      input,
      direction,
      (token) => {
        setStreamingText((prev) => prev + token);
      },
      (data) => {
        setResult({
          source_text: input,
          translated_text: data.full_text || streamingText,
          detected_language: data.detected_language || "en",
          target_language: data.target_language || "yo",
          engine: data.engine || "gpt-4o-mini",
          quality: data.quality,
          code_switched: data.code_switched || false,
        });
        setIsStreaming(false);
        setLoading(false);
      },
      (error) => {
        if (error === "canceled") {
          showToast({ message: "Translation canceled.", type: "success" });
          setIsStreaming(false);
          setLoading(false);
          return;
        }
        // Don't fall back to non-streaming mid-stream to avoid race condition
        // Instead, show error if no streaming text yet, otherwise keep what we have
        if (!streamingText) {
          translateAPI.translate(input, direction).then((res) => {
            setResult(res.data);
            setIsStreaming(false);
            setLoading(false);
          }).catch((err) => {
            showToast({ message: err.response?.data?.detail || "Translation failed.", type: "error" });
            setIsStreaming(false);
            setLoading(false);
          });
        } else {
          // Partial stream received - show what we got as the result
          showToast({ message: "Translation completed with partial streaming.", type: "error" });
          setResult({
            source_text: input,
            translated_text: streamingText,
            detected_language: "en",
            target_language: "yo",
            engine: "gpt-4o-mini",
          });
          setIsStreaming(false);
          setLoading(false);
        }
      },
      abortRef.current.signal
    );
  };

  const handleCancel = () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleTranslate();
    }
  };

  const copyText = (text: string, setCopied: (v: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Keyboard shortcuts (after all handlers are defined)
  const shortcutHandlers = useMemo(() => ({
    onTranslate: () => { if (input.trim() && !loading) handleTranslate(); },
    onCopy: () => { if (result) copyText(result.translated_text, setCopiedTranslation); },
    onToggleTheme: () => setTheme(theme === "dark" ? "light" : "dark"),
  }), [input, loading, result, theme]);
  useKeyboardShortcuts(shortcutHandlers);

  const langLabel = (code: string) => (code === "yo" ? "Yoruba" : code === "mixed" ? "Mixed" : "English");
  const langBadge = (code: string) =>
    code === "yo"
      ? "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300"
      : code === "mixed"
      ? "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300"
      : "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300";

  const wordCount = (text: string) => text.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Input section */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-5">
          <Languages className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h2 className="text-base font-semibold text-foreground">Translate</h2>
        </div>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="input-field min-h-[160px] resize-none"
          placeholder="Type or paste text in English, Yoruba, or a mix of both..."
          aria-label="Translation input"
        />

        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-muted">
            {input.trim() ? (
              `${wordCount(input)} word${wordCount(input) !== 1 ? "s" : ""} \u00B7 ${input.length} chars`
            ) : "Enter to translate \u00B7 Shift+Enter for newline"}
            {input.length > MAX_CHARS * 0.9 && input.length <= MAX_CHARS && (
              <span className="text-amber-500 dark:text-amber-400 ml-1">({MAX_CHARS - input.length} chars left)</span>
            )}
          </span>
          <button
            onClick={handleTranslate}
            disabled={loading || !input.trim()}
            className="btn-primary flex items-center justify-center gap-2 text-sm px-5 py-2.5"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4" />
            )}
            Translate
          </button>
        </div>
      </div>

      {/* Streaming output */}
      {isStreaming && (
        <div className="card p-6 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
              </span>
              <span className="text-sm font-medium text-foreground">Streaming translation</span>
            </div>
            <button
              onClick={handleCancel}
              disabled={!isStreaming}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <X className="w-3.5 h-3.5" />
              Cancel
            </button>
            <span className="text-xs text-muted font-medium">In progress</span>
          </div>
          <div
            ref={streamRef}
            className="p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 max-h-[300px] overflow-y-auto"
          >
            <p className="text-foreground text-sm leading-relaxed whitespace-pre-wrap">
              {streamingText}
              <span className="inline-block w-[2px] h-4 bg-cyan-500 animate-pulse ml-0.5 align-middle rounded-full" />
            </p>
          </div>
        </div>
      )}

      {/* Final result */}
      {result && !isStreaming && (
        <div className="card p-6 animate-fade-in">
          {/* Header with badges */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <span className={langBadge(result.detected_language)}>
                {langLabel(result.detected_language)}
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600" />
              <span className={langBadge(result.target_language)}>
                {langLabel(result.target_language)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {result.code_switched && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300">
                  <Sparkles size={10} />
                  Code-switched
                </span>
              )}
              <span className="badge badge-slate text-xs">{result.engine}</span>
              {result.quality && (
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                  result.quality === "high" ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" :
                  result.quality === "medium" ? "bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300" :
                  "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300"
                }`}>
                  <Shield size={10} />
                  {result.quality === "high" ? "High Quality" :
                   result.quality === "medium" ? "Good Quality" : "Fallback"}
                </span>
              )}
            </div>
          </div>

          {/* Source card */}
          <div className="mb-3 p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/10">
            <p className="text-[11px] text-muted uppercase tracking-wider font-semibold mb-2">Source</p>
            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{result.source_text}</p>
          </div>

          {/* Translation card */}
          <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-500/5 border border-blue-200/40 dark:border-blue-400/10 mb-4">
            <p className="text-[11px] text-blue-600 dark:text-blue-400 uppercase tracking-wider font-semibold mb-2">Translation</p>
            <p className="text-sm text-foreground leading-relaxed font-medium whitespace-pre-wrap">{result.translated_text}</p>
          </div>

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => copyText(result.source_text, setCopiedSource)}
              className="btn-secondary flex items-center justify-center gap-2 text-xs px-4 py-2.5 flex-1"
            >
              <Copy className="w-3.5 h-3.5" />
              {copiedSource ? "Copied!" : "Copy Source"}
            </button>
            <button
              onClick={() => copyText(result.translated_text, setCopiedTranslation)}
              className="btn-primary flex items-center justify-center gap-2 text-xs px-4 py-2.5 flex-1"
            >
              {copiedTranslation ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedTranslation ? "Copied!" : "Copy Translation"}
            </button>
            <a
              href={`data:text/plain;charset=utf-8,${encodeURIComponent(result.translated_text)}`}
              download="yoruba_translation.txt"
              className="btn-secondary flex items-center justify-center gap-2 text-xs px-4 py-2.5 no-underline flex-1"
            >
              <Download className="w-3.5 h-3.5" />
              TXT
            </a>
            <a
              href={`data:text/html;charset=utf-8,${encodeURIComponent(`<html><head><meta charset="UTF-8"><title>Translation</title><style>body{font-family:system-ui;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.7}p{margin:.5rem 0}</style></head><body><h1>Yoruba Translation</h1><p style="color:#666;font-size:.875rem">Generated by Bámi-Sọ̀rọ̀</p><h2>Source (${result.detected_language})</h2><p>${result.source_text}</p><h2>Translation (${result.target_language})</h2><p style="font-weight:500">${result.translated_text}</p></body></html>`)}`}
              download="yoruba_translation.html"
              className="btn-secondary flex items-center justify-center gap-2 text-xs px-4 py-2.5 no-underline flex-1"
            >
              <Download className="w-3.5 h-3.5" />
              HTML
            </a>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !isStreaming && (
        <div className="card p-12 text-center">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center mb-4">
            <Languages className="w-8 h-8 text-blue-400 dark:text-blue-500" />
          </div>
          <p className="text-sm font-semibold text-foreground">Your translation will appear here</p>
          <p className="text-xs text-muted mt-1.5">Enter English, Yoruba, or mixed text and press Enter to translate to Yoruba</p>
        </div>
      )}
    </div>
  );
}
