"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import {
  Mic, Upload, Download, Copy, Check, MicOff, RotateCcw,
  FileText, Loader2, AlertTriangle, Volume2, Play, Languages,
  Trash2, Pause, ArrowRightLeft, Square, Sparkles, Files,
} from "lucide-react";
import { transcribeAPI, correctionAPI, ttsAPI, translateAPI, TranscribeResult } from "@/lib/api";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { useTheme } from "next-themes";
import { DiffView } from "@/components/DiffView";

interface STTTabProps {
  showToast: (toast: { message: string; type: "error" | "success" }) => void;
}

function describeMicError(name: string): { key: string; title: string; message: string } {
  if (typeof window !== "undefined" && (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)) {
    return {
      key: "unsupported",
      title: "Recording not supported",
      message: "This browser doesn't support microphone access. Try Chrome, Edge, or Firefox on a laptop or phone.",
    };
  }
  switch (name) {
    case "NotAllowedError":
    case "PermissionDeniedError":
      return {
        key: "denied",
        title: "Microphone permission denied",
        message: "Allow microphone access in your browser's site settings (the padlock icon near the address bar), then try again.",
      };
    case "NotFoundError":
    case "DevicesNotFoundError":
      return {
        key: "none",
        title: "No microphone found",
        message: "We couldn't find a microphone on this device. Connect or plug one in, then try again.",
      };
    case "NotReadableError":
    case "AbortError":
    case "TrackStartError":
      return {
        key: "busy",
        title: "Microphone is in use",
        message: "Another app or browser tab is using your microphone. Close it, then try again.",
      };
    case "SecurityError":
      return {
        key: "insecure",
        title: "Secure connection required",
        message: "Microphone access requires HTTPS or localhost. This page isn't running on a secure origin.",
      };
    case "OverconstrainedError":
      return {
        key: "conflict",
        title: "Microphone settings conflict",
        message: "Your microphone can't meet the requested settings. Try a different device, then try again.",
      };
    default:
      return {
        key: "generic",
        title: "Microphone unavailable",
        message: "We couldn't access your microphone. Check that it's connected and that no recording software has it locked.",
      };
  }
}

export function STTTab({ showToast }: STTTabProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [result, setResult] = useState<TranscribeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [draftLang, setDraftLang] = useState("yo");
  const [draftWords, setDraftWords] = useState<Array<{ word: string; confidence: number; start?: number; end?: number }>>([]);
  const [draftConfidence, setDraftConfidence] = useState<number | null>(null);
  const [draftEngine, setDraftEngine] = useState("");
  const [polishing, setPolishing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [copied, setCopied] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editText, setEditText] = useState("");
  const [correcting, setCorrecting] = useState(false);
  const [translation, setTranslation] = useState("");
  const [translating, setTranslating] = useState(false);
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const [ttsAudio, setTtsAudio] = useState<HTMLAudioElement | null>(null);
  const [showRawOutput, setShowRawOutput] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [language] = useState<"auto">("auto");
  const [showDiff, setShowDiff] = useState(false);
  const [originalText, setOriginalText] = useState("");
  const [batchFiles, setBatchFiles] = useState<File[]>([]);
  const [batchResults, setBatchResults] = useState<Array<{ file: File; result?: TranscribeResult; error?: string; loading: boolean }>>([]);
  const [micError, setMicError] = useState<{ key: string; title: string; message: string } | null>(null);
  const [inputMode, setInputMode] = useState<"record" | "upload">("record");
  const { theme, setTheme } = useTheme();

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const pausedRef = useRef(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const cleanupRecording = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  }, []);

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(dataArray);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
      gradient.addColorStop(0, "#3b82f6");
      gradient.addColorStop(0.5, "#8b5cf6");
      gradient.addColorStop(1, "#3b82f6");

      ctx.lineWidth = 2.5;
      ctx.strokeStyle = gradient;
      ctx.lineCap = "round";
      ctx.beginPath();
      const sliceWidth = canvas.width / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
    };
    draw();
  }, []);

  const stopWaveform = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        cleanupRecording();
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
      drawWaveform();
      timerRef.current = setInterval(() => {
        if (!pausedRef.current) setRecordingTime((t) => t + 1);
      }, 1000);
    } catch (err: any) {
      const name = err?.name || "";
      setMicError(describeMicError(name));
      showToast({ message: describeMicError(name).title, type: "error" });
    }
  }, [drawWaveform, showToast, cleanupRecording]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setIsPaused(false);
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    stopWaveform();
  }, [stopWaveform]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.pause();
    }
    pausedRef.current = true;
    setIsPaused(true);
  }, []);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
    }
    pausedRef.current = false;
    setIsPaused(false);
  }, []);

  const deleteRecording = useCallback(() => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioBlob(null);
    setAudioUrl(null);
    setResult(null);
    setTranslation("");
    setRecordingTime(0);
    setProcessingTime(null);
    setShowRawOutput(false);
    setEditMode(false);
    setDraftText("");
    setDraftWords([]);
    setDraftConfidence(null);
    setDraftEngine("");
  }, [audioUrl]);

  const retake = useCallback(() => {
    deleteRecording();
  }, [deleteRecording]);

  const dismissMicError = () => setMicError(null);

  const retryMic = () => {
    setMicError(null);
    startRecording();
  };

  // Step 1: convert audio to a raw draft only. No code-switch resolution,
  // no tone restoration, no review — the user sees exactly what the speech
  // engine heard before deciding whether to translate or transcribe/polish.
  const handleConvertToDraft = useCallback(
    async (blob?: Blob) => {
      const file = blob || audioBlob;
      if (!file) return;
      setLoading(true);
      setResult(null);
      setTranslation("");
      setDraftText("");
      setProcessingTime(null);
      const startTime = Date.now();
      try {
        const filename = blob ? (blob instanceof File ? blob.name : "recording.webm") : "recording.webm";
        const res = await transcribeAPI.draftOnly(file, filename, language);
        setDraftText(res.data.raw_text || "");
        setDraftLang(res.data.detected_language || "yo");
        setDraftWords(res.data.word_confidences || []);
        setDraftConfidence(res.data.confidence);
        setDraftEngine(res.data.engine || "");
        setProcessingTime(Math.round((Date.now() - startTime) / 1000));
      } catch (err: any) {
        showToast({ message: err.response?.data?.detail || "Speech-to-text failed", type: "error" });
      } finally {
        setLoading(false);
      }
    },
    [audioBlob, showToast, language]
  );

  // Step 2 (polish): apply code-switch + tone restoration + orthographic
  // review to the user-confirmed draft text.
  const handlePolishDraft = useCallback(async () => {
    const text = draftText.trim();
    if (!text) return;
    setPolishing(true);
    try {
      const res = await transcribeAPI.polish(text, draftLang);
      const polished = res.data?.text ?? text;
      const synthetic: TranscribeResult = {
        raw_text: text,
        final_text: polished,
        confidence: null,
        word_confidences: [],
        quality: null,
        id: 0,
        created_at: new Date().toISOString(),
        detected_language: draftLang,
        engine: "polish",
        code_switched: false,
      };
      setOriginalText(text);
      setResult(synthetic);
    } catch (err: any) {
      showToast({ message: err.response?.data?.detail || "Polish failed", type: "error" });
    } finally {
      setPolishing(false);
    }
  }, [draftText, draftLang, showToast]);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("audio/")) {
        showToast({ message: "Please upload an audio file", type: "error" });
        return;
      }
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioBlob(file);
      setAudioUrl(URL.createObjectURL(file));
      setResult(null);
      setTranslation("");
      setDraftText("");
      setDraftWords([]);
      setDraftConfidence(null);
      setDraftEngine("");
      setProcessingTime(null);
      await handleConvertToDraft(file);
    },
    [showToast, handleConvertToDraft, audioUrl]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length === 1) {
        handleFile(files[0]);
      } else if (files.length > 1) {
        handleBatchUpload(files);
      }
    },
    [handleFile]
  );

  const handleBatchUpload = useCallback(
    async (files: File[]) => {
      const audioFiles = files.filter(f => f.type.startsWith("audio/"));
      if (audioFiles.length === 0) {
        showToast({ message: "No audio files found", type: "error" });
        return;
      }
      setBatchFiles(audioFiles);
      setBatchResults(audioFiles.map(f => ({ file: f, loading: true })));

      for (let i = 0; i < audioFiles.length; i++) {
        try {
          const res = await transcribeAPI.transcribe(audioFiles[i], audioFiles[i].name, language);
          setBatchResults(prev => prev.map((r, idx) =>
            idx === i ? { ...r, result: res.data, loading: false } : r
          ));
        } catch (err: any) {
          setBatchResults(prev => prev.map((r, idx) =>
            idx === i ? { ...r, error: err.response?.data?.detail || "Failed", loading: false } : r
          ));
        }
      }
    },
    [showToast, language]
  );

  const handleCopy = useCallback(
    async (text: string) => {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      showToast({ message: "Copied to clipboard", type: "success" });
      setTimeout(() => setCopied(false), 2000);
    },
    [showToast]
  );

  const handleDownload = useCallback((text: string, filename: string) => {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleExportSRT = useCallback((text: string) => {
    const words = text.split(/\s+/);
    const wordsPerSegment = 8;
    let srt = "";
    for (let i = 0; i < words.length; i += wordsPerSegment) {
      const chunk = words.slice(i, i + wordsPerSegment).join(" ");
      const startSec = (i / wordsPerSegment) * 2;
      const endSec = startSec + 2;
      const formatTime = (s: number) => {
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = Math.floor(s % 60);
        const ms = Math.floor((s % 1) * 1000);
        return `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")},${String(ms).padStart(3,"0")}`;
      };
      srt += `${Math.floor(i / wordsPerSegment) + 1}\n${formatTime(startSec)} --> ${formatTime(endSec)}\n${chunk}\n\n`;
    }
    handleDownload(srt, `transcription-${Date.now()}.srt`);
  }, [handleDownload]);

  const handleExportHTML = useCallback((text: string) => {
    const html = `<!DOCTYPE html><html lang="yo"><head><meta charset="UTF-8"><title>Transcription</title><style>body{font-family:system-ui;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.7}p{margin:.5rem 0}</style></head><body><h1>Transcription</h1><div class="meta" style="color:#666;font-size:.875rem">Generated by Bámi-Sọ̀rọ̀</div>${text.split("\n").map(p => `<p>${p}</p>`).join("")}</body></html>`;
    handleDownload(html, `transcription-${Date.now()}.html`);
  }, [handleDownload]);

  const handleTTS = useCallback(
    async (text: string, lang: string) => {
      if (ttsPlaying && ttsAudio) {
        ttsAudio.pause();
        setTtsPlaying(false);
        setTtsAudio(null);
        return;
      }
      try {
        const blob = await ttsAPI.synthesize(text, lang);
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        setTtsAudio(audio);
        setTtsPlaying(true);
        audio.onended = () => { setTtsPlaying(false); setTtsAudio(null); };
        audio.play().catch(() => {});
      } catch {
        showToast({ message: "TTS playback failed", type: "error" });
      }
    },
    [ttsPlaying, ttsAudio, showToast]
  );

  const handleTTSDownload = useCallback(
    async (text: string, lang: string) => {
      try {
        const blob = await ttsAPI.synthesize(text, lang);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `transcription-audio-${Date.now()}.${blob.type.includes("mp3") ? "mp3" : "wav"}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast({ message: "Audio downloaded", type: "success" });
      } catch {
        showToast({ message: "TTS download failed", type: "error" });
      }
    },
    [showToast]
  );

  const handleTranslate = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      setTranslating(true);
      try {
        const res = await translateAPI.translate(text, "auto");
        setTranslation(res.data.translated_text);
      } catch {
        showToast({ message: "Translation failed", type: "error" });
      } finally {
        setTranslating(false);
      }
    },
    [showToast]
  );

  const handleSaveCorrection = useCallback(async () => {
    if (!result || !editText.trim()) return;
    setCorrecting(true);
    try {
      if (result.id && result.id > 0) {
        await correctionAPI.save(result.id, editText);
      }
      setResult({ ...result, final_text: editText });
      setEditMode(false);
      showToast({ message: result.id && result.id > 0 ? "Correction saved" : "Text updated", type: "success" });
    } catch {
      showToast({ message: "Failed to save correction", type: "error" });
    } finally {
      setCorrecting(false);
    }
  }, [result, editText, showToast]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stopWaveform();
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      if (ttsAudio) { ttsAudio.pause(); }
      cleanupRecording();
    };
  }, [stopWaveform, audioUrl, ttsAudio, cleanupRecording]);

  // Keyboard shortcuts (after all handlers are defined)
  const shortcutHandlers = useMemo(() => ({
    onTranscribe: () => { if (audioBlob && !loading) handleConvertToDraft(); },
    onCopy: () => { if (result) handleCopy(result.final_text); },
    onNewRecording: () => { if (!isRecording) startRecording(); },
    onToggleTheme: () => setTheme(theme === "dark" ? "light" : "dark"),
  }), [audioBlob, loading, handleConvertToDraft, result, handleCopy, isRecording, startRecording, theme, setTheme]);
  useKeyboardShortcuts(shortcutHandlers);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const renderHighlightedText = (words: Array<{ word: string; confidence: number; start?: number; end?: number }>) => {
    const avgConf = words.reduce((sum, w) => sum + w.confidence, 0) / words.length;
    const hasTimestamps = words.some((w) => typeof w.start === "number");
    return (
      <div className="flex flex-wrap gap-0.5 leading-relaxed">
        {words.map((w, i) => {
          const normalized = avgConf > 0 ? w.confidence / avgConf : w.confidence;
          let cls = "";
          if (normalized < 0.7) cls = "bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-b-2 border-red-300 dark:border-red-500/40 font-medium";
          else if (normalized < 0.9) cls = "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400";
          const hint = typeof w.start === "number" ? ` (${formatTime(w.start)}${typeof w.end === "number" ? `–${formatTime(w.end)}` : ""})` : "";
          return (
            <span key={i} className={`${cls} px-0.5 rounded-sm`} title={`${(w.confidence * 100).toFixed(0)}%${hint}`}>
              {w.word}{" "}
            </span>
          );
        })}
      </div>
    );
  };

  // Draft confidence renderer: uses ABSOLUTE thresholds so the user sees
  // which words the ASR engine itself was unsure about (red < 0.7 →
  // likely misrecognized, amber < 0.9 → uncertain). This pins down where
  // speech-recognition errors originate before translation/transcription.
  const renderDraftConfidence = (words: Array<{ word: string; confidence: number; start?: number; end?: number }>) => {
    return (
      <div className="flex flex-wrap gap-0.5 leading-relaxed">
        {words.map((w, i) => {
          let cls = "";
          if (w.confidence < 0.7) cls = "bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-b-2 border-red-300 dark:border-red-500/40 font-medium";
          else if (w.confidence < 0.9) cls = "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400";
          const hint = typeof w.start === "number" ? ` (${formatTime(w.start)}${typeof w.end === "number" ? `–${formatTime(w.end)}` : ""})` : "";
          return (
            <span key={i} className={`${cls} px-0.5 rounded-sm`} title={`${(w.confidence * 100).toFixed(0)}%${hint}`}>
              {w.word}{" "}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* ── Workflow Step Indicator ── */}
      {(result || draftText || loading) && (
        <div className="flex items-center justify-center gap-4 px-4">
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              (result || draftText || audioBlob) ? "bg-blue-600 text-white" : "bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400"
            }`}>1</div>
            <span className="text-xs font-medium text-muted">Input</span>
          </div>
          <div className={`flex-1 h-0.5 ${draftText || result ? "bg-blue-600" : "bg-border"}`} />
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              draftText ? "bg-blue-600 text-white" : "bg-slate-200 dark:bg-slate-700 text-slate-400"
            }`}>2</div>
            <span className="text-xs font-medium text-muted">Review</span>
          </div>
          <div className={`flex-1 h-0.5 ${result ? "bg-blue-600" : "bg-border"}`} />
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              result ? "bg-blue-600 text-white" : "bg-slate-200 dark:bg-slate-700 text-slate-400"
            }`}>3</div>
            <span className="text-xs font-medium text-muted">Result</span>
          </div>
        </div>
      )}

      {/* ── Unified Input Card ── */}
      {!result && !loading && (
        <div className="card p-6">
          {/* Mode Toggle — only when no audio is captured yet */}
          {!audioBlob && !isRecording && (
            <div className="flex justify-center mb-6">
              <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800/50 border border-border">
                <button
                  onClick={() => setInputMode("record")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    inputMode === "record"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-muted hover:text-foreground hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  <Mic size={14} className="inline mr-1.5" />
                  Record
                </button>
                <button
                  onClick={() => setInputMode("upload")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    inputMode === "upload"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-muted hover:text-foreground hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  <Upload size={14} className="inline mr-1.5" />
                  Upload
                </button>
              </div>
            </div>
          )}

          {/* Recording Mode */}
          {(inputMode === "record" || isRecording || audioBlob) && (
            <div>
              <div className="mb-4 text-center">
                <h3 className="text-sm font-semibold text-foreground flex items-center justify-center gap-2">
                  <Mic size={16} className="text-blue-600 dark:text-blue-400" />
                  Record Audio
                </h3>
                <p className="text-xs text-muted mt-1">
                  Speak Yorùbá or English. We automatically detect the language and handle code-switching mid-sentence.
                </p>
              </div>

              {isRecording ? (
                <div className="space-y-5">
                  <div className="relative">
                    <canvas
                      ref={canvasRef}
                      width={600}
                      height={100}
                      className="w-full h-24 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10"
                    />
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="recording-pulse" />
                    </div>
                  </div>

                  <div className="flex items-center justify-center gap-3">
                    {isPaused ? (
                      <span className="flex items-center gap-2 text-amber-500 dark:text-amber-400">
                        <Pause size={16} />
                        <span className="text-sm font-medium">Paused</span>
                      </span>
                    ) : (
                      <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse-dot" />
                    )}
                    <span className={`text-3xl font-mono font-bold tabular-nums ${isPaused ? "text-amber-500 dark:text-amber-400" : "text-red-500 dark:text-red-400"}`}>
                      {formatTime(recordingTime)}
                    </span>
                  </div>

                  <div className="flex gap-2.5">
                    <button
                      onClick={isPaused ? resumeRecording : pauseRecording}
                      className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium transition-all active:scale-[0.98] shadow-lg ${
                        isPaused
                          ? "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-emerald-500/20 hover:shadow-emerald-500/30"
                          : "bg-white dark:bg-white/10 border border-slate-200 dark:border-white/15 text-foreground hover:bg-slate-50 dark:hover:bg-white/15"
                      }`}
                    >
                      {isPaused ? (
                        <>
                          <Play size={18} />
                          Resume
                        </>
                      ) : (
                        <>
                          <Pause size={18} />
                          Pause
                        </>
                      )}
                    </button>
                    <button
                      onClick={stopRecording}
                      className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl font-medium transition-all shadow-lg shadow-red-500/20 hover:shadow-red-500/30 active:scale-[0.98]"
                    >
                      <MicOff size={18} />
                      Stop Recording
                    </button>
                  </div>
                </div>
              ) : audioBlob ? (
                <div className="space-y-4">
                  <div className="relative group">
                    <audio src={audioUrl ?? ""} controls className="w-full h-12 rounded-xl" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-muted">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      <span className="font-medium">{formatTime(recordingTime)}</span>
                      <span className="text-slate-300 dark:text-slate-600">|</span>
                      <span>{(audioBlob.size / 1024).toFixed(0)} KB</span>
                    </div>
                    <button
                      onClick={deleteRecording}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-all"
                    >
                      <Trash2 size={13} />
                      Delete
                    </button>
                  </div>

                  <div className="flex gap-2.5">
                    <button
                      onClick={() => handleConvertToDraft()}
                      disabled={loading}
                      className="btn-primary flex-1 py-3"
                    >
                      {loading ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <FileText size={16} />
                      )}
                      {loading ? "Converting to text..." : "Convert To Text"}
                    </button>
                    <button onClick={retake} className="btn-secondary px-4 py-3">
                      <RotateCcw size={16} />
                    </button>
                  </div>
                  <p className="text-xs text-muted flex items-center gap-1.5">
                    <Sparkles size={12} className="text-blue-500" />
                    Step 1 — review the raw speech text, then translate or transcribe from there.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {micError && (
                    <div className="rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/10 p-4">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-500 dark:text-red-400 shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-red-700 dark:text-red-300">{micError.title}</p>
                          <p className="text-xs text-red-600/90 dark:text-red-300/80 mt-0.5">{micError.message}</p>
                          {micError.key === "denied" && (
                            <p className="text-xs text-red-600/80 dark:text-red-300/60 mt-1.5">
                              Still blocked? Check OS-level privacy settings — Windows: Settings → Privacy →
                              Microphone · macOS: System Settings → Privacy &amp; Security → Microphone.
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center justify-end gap-2 mt-3">
                        <button
                          onClick={dismissMicError}
                          className="text-xs px-3 py-1.5 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-100/60 dark:hover:bg-red-500/10 transition-colors"
                        >
                          Dismiss
                        </button>
                        <button
                          onClick={retryMic}
                          className="text-xs px-3 py-1.5 rounded-lg font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
                        >
                          Try again
                        </button>
                      </div>
                    </div>
                  )}
                  <button
                    onClick={() => { setMicError(null); startRecording(); }}
                    className="record-button w-full flex items-center justify-center gap-3 p-10 rounded-2xl transition-all group"
                  >
                    <div className="record-button-inner w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center group-hover:from-blue-600 group-hover:to-blue-700 transition-all shadow-xl shadow-blue-500/30 group-hover:shadow-blue-500/40 group-active:scale-95">
                      <Mic size={28} className="text-white" />
                    </div>
                  </button>
                  <div className="text-center">
                    <p className="text-xs text-muted font-medium">Tap to start recording</p>
                    <p className="text-xs text-muted mt-1.5 max-w-xs mx-auto">
                      Records in WebM/Opus format. Supports up to 5 minutes per session.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Mode */}
          {inputMode === "upload" && !isRecording && !audioBlob && (
            <div>
              <div className="mb-4 text-center">
                <h3 className="text-sm font-semibold text-foreground flex items-center justify-center gap-2">
                  <Upload size={16} className="text-blue-600 dark:text-blue-400" />
                  Upload Audio
                </h3>
                <p className="text-xs text-muted mt-1">
                  Upload pre-recorded audio files for transcription
                </p>
              </div>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                  dragOver
                    ? "border-blue-400 bg-blue-50 dark:bg-blue-500/10 scale-[1.01]"
                    : "border-slate-200 dark:border-white/10 hover:border-blue-300 dark:hover:border-blue-500/30 hover:bg-blue-50/50 dark:hover:bg-blue-500/5"
                }`}
              >
                <div className="flex flex-col items-center gap-3">
                  <Upload size={28} className="text-slate-400 dark:text-slate-500" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-1">
                      Drag and drop or <span className="text-blue-600 dark:text-blue-400">browse</span> files
                    </p>
                    <p className="text-xs text-muted">
                      WAV, MP3, WebM, OGG up to 25MB · Multiple files supported
                    </p>
                  </div>
                </div>
                <input ref={fileInputRef} type="file" accept="audio/*" multiple className="hidden" onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  if (files.length === 1) handleFile(files[0]);
                  else if (files.length > 1) handleBatchUpload(files);
                  e.target.value = "";
                }} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Draft Review — Step 2: user reads/edits the raw speech text before
          deciding to translate or polish. Isolates ASR errors from
          translation/transcription errors. */}
      {draftText && !loading && !polishing && !result && (
        <div className="card p-6 animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FileText size={16} className="text-blue-600 dark:text-blue-400" />
                Draft text (from speech)
              </h3>
              <p className="text-xs text-muted mt-0.5">
                Review and edit the raw speech-to-text output before translating or polishing.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {draftEngine && <span className="badge badge-slate">{draftEngine}</span>}
              {draftConfidence != null && draftConfidence > 0 && (
                <span className={`badge ${draftConfidence >= 0.7 ? "badge-green" : draftConfidence >= 0.5 ? "badge-amber" : "badge-red"}`}>
                  {(draftConfidence * 100).toFixed(0)}% confident
                </span>
              )}
              {processingTime !== null && <span className="text-xs text-muted">{processingTime}s</span>}
            </div>
          </div>
          <p className="text-xs text-muted mb-4">
            This is the raw text the speech engine heard — before any tone-mark, code-switch
            or orthography fixes. Check where recognition went wrong, edit if needed, then
            translate or transcribe (polish) it.
          </p>

          {draftConfidence != null && draftConfidence < 0.7 && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl text-amber-700 dark:text-amber-400 text-sm mb-4">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-medium">Low confidence ({(draftConfidence * 100).toFixed(0)}%) — the engine may have misheard words.</p>
                <ul className="text-xs mt-1 space-y-0.5 list-disc list-inside text-amber-600 dark:text-amber-400/80">
                  <li>Red words below are likely wrong — double-check them</li>
                  <li>Record again in a quieter spot if most words are red</li>
                </ul>
              </div>
            </div>
          )}

          {draftWords.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-muted mb-2">
                Unclear words are highlighted — <span className="text-red-500">red = likely misheard</span>,{" "}
                <span className="text-amber-600 dark:text-amber-400">amber = uncertain</span>. Hover for details.
              </p>
              <div className="p-3 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-sm text-foreground leading-relaxed">
                {renderDraftConfidence(draftWords)}
              </div>
            </div>
          )}

          <textarea
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            className="input-field min-h-[100px] resize-none mb-4"
            autoFocus
          />

          <div className="flex flex-wrap gap-2.5">
            <button
              onClick={() => handleTranslate(draftText)}
              disabled={translating || !draftText.trim()}
              className="btn-primary flex-1 py-2.5 min-w-[140px]"
            >
              {translating ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <ArrowRightLeft size={15} />
              )}
              {translating ? "Translating..." : "Translate"}
            </button>
            <button
              onClick={handlePolishDraft}
              disabled={polishing || !draftText.trim()}
              className="btn-primary flex-1 py-2.5 min-w-[140px] bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 shadow-purple-500/20 hover:shadow-purple-500/30"
            >
              {polishing ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <Sparkles size={15} />
              )}
              {polishing ? "Polishing..." : "Transcribe & fix tone marks"}
            </button>
          </div>
        </div>
      )}

      {/* Translation of the draft */}
      {draftText && translation && !result && !translating && (
        <div className="card p-6 bg-blue-50/50 dark:bg-blue-500/5 border-blue-200 dark:border-blue-500/15 animate-fade-in">
          <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2 flex items-center gap-2">
            <Languages size={14} />
            Translation
          </h4>
          <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{translation}</p>
          <div className="flex items-center gap-2 mt-3">
            <button onClick={() => handleCopy(translation)} className="btn-ghost text-xs">
              <Copy size={14} /> Copy
            </button>
          </div>
        </div>
      )}

      {/* Batch Results */}
      {batchResults.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Files size={16} className="text-blue-600 dark:text-blue-400" />
              Batch Results ({batchResults.length} files)
            </h3>
            <button
              onClick={() => { setBatchFiles([]); setBatchResults([]); }}
              className="text-xs text-muted hover:text-foreground"
            >
              Clear all
            </button>
          </div>
          <div className="space-y-3">
            {batchResults.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-foreground truncate">{item.file.name}</span>
                  {item.loading && <Loader2 size={12} className="animate-spin text-blue-500" />}
                  {item.result && <Check size={12} className="text-green-500" />}
                  {item.error && <AlertTriangle size={12} className="text-red-500" />}
                </div>
                {item.result && (
                  <p className="text-sm text-foreground leading-relaxed">{item.result.final_text}</p>
                )}
                {item.error && (
                  <p className="text-xs text-red-500">{item.error}</p>
                )}
              </div>
            ))}
          </div>
          {batchResults.some(r => r.result) && (
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => {
                  const allText = batchResults
                    .filter(r => r.result)
                    .map((r, i) => `--- ${r.file.name} ---\n${r.result!.final_text}`)
                    .join("\n\n");
                  const blob = new Blob([allText], { type: "text/plain" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `batch-transcription-${Date.now()}.txt`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="btn-secondary text-xs flex items-center gap-1.5"
              >
                <Download size={12} /> Download All
              </button>
              <button
                onClick={() => {
                  const allText = batchResults
                    .filter(r => r.result)
                    .map(r => r.result!.final_text)
                    .join("\n");
                  navigator.clipboard.writeText(allText);
                  showToast({ message: "All transcriptions copied", type: "success" });
                }}
                className="btn-ghost text-xs flex items-center gap-1.5"
              >
                <Copy size={12} /> Copy All
              </button>
            </div>
          )}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="card p-6 space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <Loader2 size={16} className="animate-spin text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-foreground">Analyzing audio...</span>
          </div>
          <div className="skeleton h-4 w-3/4" />
          <div className="skeleton h-4 w-1/2" />
          <div className="skeleton h-4 w-2/3" />
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <div className="space-y-4 animate-fade-in">
          <div className="card p-6">
            {/* Badges */}
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <span className="badge badge-blue">
                <Languages size={12} />
                Auto
                {result.detected_language === "yo" ? " (Yoruba)" :
                 result.detected_language === "en" ? " (English)" :
                 result.detected_language === "mixed" ? " (Mixed)" : ""}
              </span>
              {result.code_switched && (
                <span className="badge badge-purple">
                  <Sparkles size={12} />
                  Code-switched
                </span>
              )}
              {result.engine && <span className="badge badge-slate">{result.engine}</span>}
              {processingTime !== null && <span className="text-xs text-muted">{processingTime}s</span>}
            </div>

            {/* Confidence */}
            {result.confidence != null && result.confidence > 0 && (
              <div className="mb-4">
                <div className="flex items-center justify-between text-xs text-foreground mb-1.5">
                  <span className="font-medium">Confidence</span>
                  <span className="font-mono">{(result.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-100 dark:bg-white/5 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${
                    result.confidence >= 0.75 ? "bg-green-500" : result.confidence >= 0.5 ? "bg-amber-500" : "bg-red-500"
                  }`} style={{ width: `${result.confidence * 100}%` }} />
                </div>
              </div>
            )}

            {result.confidence != null && result.confidence > 0 && result.confidence < 0.5 && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl text-amber-700 dark:text-amber-400 text-sm mb-4">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium">Low confidence ({(result.confidence * 100).toFixed(0)}%)</p>
                  <ul className="text-xs mt-1 space-y-0.5 list-disc list-inside text-amber-600 dark:text-amber-400/80">
                    <li>Speak clearly and reduce background noise</li>
                    <li>Hold the microphone closer to your mouth</li>
                    <li>Try speaking at a moderate pace</li>
                  </ul>
                </div>
              </div>
            )}

            {/* Quality Warnings */}
            {result.quality?.warnings && result.quality.warnings.length > 0 && (
              <div className="mb-4 space-y-1.5">
                {result.quality.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-xs text-muted">
                    <AlertTriangle size={12} className="mt-0.5 shrink-0" />
                    {w}
                  </div>
                ))}
              </div>
            )}

            {/* Side-by-side diff (when corrected text differs from original) */}
            {showDiff && originalText && result.final_text !== originalText && (
              <div className="mb-4">
                <DiffView original={originalText} corrected={result.final_text} />
              </div>
            )}

            {/* Diff toggle */}
            {originalText && result.final_text !== originalText && (
              <button
                onClick={() => setShowDiff(!showDiff)}
                className="mb-3 text-xs text-muted hover:text-foreground flex items-center gap-1.5 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                {showDiff ? "Hide diff" : "Show diff"}
              </button>
            )}

            {/* Text */}
            <div className="mb-4">
              {editMode ? (
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="input-field min-h-[120px] resize-none"
                  autoFocus
                />
              ) : (
                <div className="p-4 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                  {result.word_confidences.length > 0
                    ? renderHighlightedText(result.word_confidences)
                    : result.final_text}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-1.5">
              <button onClick={() => handleTTS(result.final_text, "yo")} className="btn-ghost text-xs">
                {ttsPlaying ? <Pause size={14} /> : <Play size={14} />}
                {ttsPlaying ? "Stop" : "Listen"}
              </button>
              <button onClick={() => handleTTSDownload(result.final_text, "yo")} className="btn-ghost text-xs">
                <Volume2 size={14} /> Audio
              </button>
              <button onClick={() => handleTranslate(result.final_text)} disabled={translating} className="btn-ghost text-xs">
                {translating ? <Loader2 size={14} className="animate-spin" /> : <ArrowRightLeft size={14} />}
                Translate
              </button>
              <button onClick={() => handleCopy(result.final_text)} className="btn-ghost text-xs">
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy"}
              </button>
              <button onClick={() => handleDownload(result.final_text, `transcription-${Date.now()}.txt`)} className="btn-ghost text-xs">
                <Download size={14} /> Download
              </button>
              <div className="relative group">
                <button className="btn-ghost text-xs">
                  <FileText size={14} /> Export
                </button>
                <div className="absolute right-0 top-full mt-1 w-36 bg-card border border-border rounded-xl shadow-lg py-1 z-50 hidden group-hover:block">
                  <button onClick={() => handleDownload(result.final_text, `transcription-${Date.now()}.txt`)} className="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-100 dark:hover:bg-white/5 text-foreground">Plain Text (.txt)</button>
                  <button onClick={() => handleExportSRT(result.final_text)} className="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-100 dark:hover:bg-white/5 text-foreground">Subtitles (.srt)</button>
                  <button onClick={() => handleExportHTML(result.final_text)} className="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-100 dark:hover:bg-white/5 text-foreground">HTML (.html)</button>
                </div>
              </div>
              {editMode ? (
                <>
                  <button onClick={handleSaveCorrection} disabled={correcting} className="btn-primary text-xs">
                    {correcting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                    Save
                  </button>
                  <button onClick={() => { setEditMode(false); setEditText(result.final_text); }} className="btn-secondary text-xs">Cancel</button>
                </>
              ) : (
                <button onClick={() => { setEditMode(true); setEditText(result.final_text); }} className="btn-ghost text-xs">
                  <RotateCcw size={14} /> Edit
                </button>
              )}
            </div>
          </div>

          {/* Translation */}
          {(translation || translating) && (
            <div className="card p-6 bg-blue-50/50 dark:bg-blue-500/5 border-blue-200 dark:border-blue-500/15">
              <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2 flex items-center gap-2">
                <Languages size={14} />
                Translation
              </h4>
              {translating ? (
                <div className="space-y-2">
                  <div className="skeleton h-3 w-full" />
                  <div className="skeleton h-3 w-3/4" />
                </div>
              ) : (
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{translation}</p>
              )}
              {translation && (
                <div className="flex items-center gap-2 mt-3">
                  <button onClick={() => handleCopy(translation)} className="btn-ghost text-xs">
                    <Copy size={14} /> Copy
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Raw output */}
          {result.raw_text && result.raw_text !== result.final_text && (
            <div className="card overflow-hidden">
              <button onClick={() => setShowRawOutput(!showRawOutput)} className="w-full flex items-center justify-between p-4 text-sm font-medium text-foreground hover-row transition-colors">
                <span className="flex items-center gap-2"><FileText size={14} className="text-muted" /> Raw ASR Output</span>
                <svg className={`w-4 h-4 text-muted transition-transform ${showRawOutput ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showRawOutput && (
                <div className="px-4 pb-4">
                  <pre className="p-3 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-xs text-muted overflow-x-auto whitespace-pre-wrap">{result.raw_text}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !audioBlob && !isRecording && !batchResults.length && (
        <div className="card p-12 text-center animate-fade-in">
          <div className="w-20 h-20 mx-auto rounded-3xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-5 shadow-xl shadow-blue-500/25">
            <Mic size={32} className="text-white" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Your transcription will appear here
          </h3>
          <p className="text-sm text-muted mb-6 max-w-sm mx-auto">
            Record audio with your microphone or upload an audio file to begin transcribing Yorùbá or English speech.
          </p>
          <button
            onClick={() => { setMicError(null); startRecording(); }}
            className="btn-primary flex items-center gap-2 mx-auto"
          >
            <Mic size={16} />
            Start Recording
          </button>
        </div>
      )}
    </div>
  );
}
