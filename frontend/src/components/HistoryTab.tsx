"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { historyAPI, correctionAPI, HistoryItem, ActivityType } from "@/lib/api";
import {
  Mic,
  Languages,
  Clock,
  Trash2,
  Zap,
  Search,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Download,
  Pin,
  Pencil,
  Play,
  RefreshCw,
  X,
  Headphones,
  Check,
  ArrowRightLeft,
} from "lucide-react";

interface HistoryTabProps {
  showToast: (t: { message: string; type: "error" | "success" }) => void;
}

type FilterTab = "all" | "stt" | "translation";

const PAGE_SIZE = 10;

const ENGINE_OPTIONS = [
  { value: "auto", label: "Automatic (best available)" },
  { value: "openai", label: "OpenAI (gpt-4o-transcribe / whisper)" },
  { value: "local-w2v", label: "Local W2V-BERT Yoruba" },
  { value: "local-whisper", label: "Local Whisper Yoruba" },
];

const LANGUAGE_OPTIONS = [
  { value: "auto", label: "Auto-detect" },
  { value: "yo", label: "Yorùbá" },
  { value: "en", label: "English" },
];

const DIRECTION_OPTIONS = [
  { value: "auto", label: "Auto-detect" },
  { value: "en2yo", label: "English → Yorùbá" },
  { value: "yo2en", label: "Yorùbá → English" },
];

function relativeTime(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return new Date(ts).toLocaleDateString();
}

function SkeletonRow() {
  return (
    <div className="flex items-start gap-3 py-4 animate-pulse">
      <div className="w-16 h-5 bg-slate-200 dark:bg-white/10 rounded" />
      <div className="flex-1 space-y-2">
        <div className="w-24 h-3 bg-slate-200 dark:bg-white/10 rounded" />
        <div className="w-3/4 h-4 bg-slate-200 dark:bg-white/10 rounded" />
      </div>
      <div className="w-12 h-4 bg-slate-200 dark:bg-white/10 rounded" />
    </div>
  );
}

interface RedoModalProps {
  item: HistoryItem;
  onClose: () => void;
  onDone: (result: any) => void;
  onError: (msg: string) => void;
  showToast: (t: { message: string; type: "error" | "success" }) => void;
}

function RedoModal({ item, onClose, onDone, onError, showToast }: RedoModalProps) {
  const [language, setLanguage] = useState("auto");
  const [engine, setEngine] = useState("auto");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const resp = await historyAPI.retranscribe(item.id, language, engine);
      onDone(resp.data);
    } catch (err: any) {
      onError(err.response?.data?.detail || "Re-transcription failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="glass rounded-2xl p-6 w-full max-w-md animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-bold text-foreground">Re-transcribe</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-secondary mb-5">
          Run the pipeline again on the stored audio. You can pick a different engine
          if the first result wasn&apos;t good enough.
        </p>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} className="input-field">
              {LANGUAGE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">Engine</label>
            <select value={engine} onChange={(e) => setEngine(e.target.value)} className="input-field">
              {ENGINE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              {loading ? "Processing..." : "Re-transcribe"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface RetranslateModalProps {
  item: HistoryItem;
  onClose: () => void;
  onDone: (result: any) => void;
  onError: (msg: string) => void;
}

function RetranslateModal({ item, onClose, onDone, onError }: RetranslateModalProps) {
  const [direction, setDirection] = useState("auto");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const resp = await historyAPI.retranslate(item.id, direction);
      onDone(resp.data);
    } catch (err: any) {
      onError(err.response?.data?.detail || "Re-translation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="glass rounded-2xl p-6 w-full max-w-md animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h2 className="text-lg font-bold text-foreground">Re-translate</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-secondary mb-5">
          Re-run translation on the stored text. The result will be saved as a
          new translation in your history.
        </p>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">Direction</label>
            <select value={direction} onChange={(e) => setDirection(e.target.value)} className="input-field">
              {DIRECTION_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRightLeft className="w-4 h-4" />}
              {loading ? "Processing..." : "Re-translate"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function HistoryTab({ showToast }: HistoryTabProps) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterTab>("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [exporting, setExporting] = useState(false);

  // Rename
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  // Audio playback
  const [audioUrls, setAudioUrls] = useState<Record<number, string>>({});
  const [audioLoadingId, setAudioLoadingId] = useState<number | null>(null);
  const [expandedAudioId, setExpandedAudioId] = useState<number | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  // Expand row
  const [expandedItemId, setExpandedItemId] = useState<number | null>(null);
  // Redo
  const [redoItem, setRedoItem] = useState<HistoryItem | null>(null);
  // Re-translate
  const [retranslateItem, setRetranslateItem] = useState<HistoryItem | null>(null);
  const audioUrlsRef = useRef<Record<number, string>>({});

  useEffect(() => {
    return () => {
      Object.values(audioUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  async function handleExportCorrections() {
    setExporting(true);
    try {
      const resp = await correctionAPI.export();
      const data = resp.data;
      if (data.total === 0) {
        showToast({ message: "No corrections to export", type: "error" });
        return;
      }
      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `corrections-training-data-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast({ message: `Exported ${data.total} corrections`, type: "success" });
    } catch {
      showToast({ message: "Failed to export corrections", type: "error" });
    } finally {
      setExporting(false);
    }
  }

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const typeFilter: ActivityType | undefined =
        filter === "stt"
          ? "transcription"
          : filter === "translation"
            ? "translation"
            : undefined;

      const resp = await historyAPI.list(page, PAGE_SIZE, typeFilter, searchQuery || undefined);
      const data = resp.data;
      setItems(data.items);
      setTotalPages(Math.ceil(data.total / PAGE_SIZE) || 1);
      setTotalItems(data.total);
    } catch {
      showToast({ message: "Failed to load history", type: "error" });
    } finally {
      setLoading(false);
    }
  }, [page, filter, searchQuery, showToast]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    setPage(1);
  }, [filter, searchQuery]);

  async function handleDelete(id: number) {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id);
      return;
    }

    setDeletingId(id);
    try {
      await historyAPI.delete(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotalItems((prev) => prev - 1);
      setConfirmDeleteId(null);
      const url = audioUrlsRef.current[id];
      if (url) URL.revokeObjectURL(url);
      showToast({ message: "Activity deleted", type: "success" });
    } catch {
      showToast({ message: "Failed to delete activity", type: "error" });
    } finally {
      setDeletingId(null);
    }
  }

  async function togglePin(item: HistoryItem) {
    setUpdatingId(item.id);
    try {
      const resp = await historyAPI.update(item.id, { pinned: !item.pinned });
      const updated = resp.data;
      setItems((prev) => prev.map((it) => (it.id === updated.id ? updated : it)));
      showToast({ message: updated.pinned ? "Pinned to top" : "Unpinned", type: "success" });
    } catch {
      showToast({ message: "Failed to update item", type: "error" });
    } finally {
      setUpdatingId(null);
    }
  }

  async function saveTitle(id: number) {
    setUpdatingId(id);
    try {
      const resp = await historyAPI.update(id, { title: draftTitle || null });
      const updated = resp.data;
      setItems((prev) => prev.map((it) => (it.id === updated.id ? updated : it)));
    } catch {
      showToast({ message: "Failed to rename item", type: "error" });
    } finally {
      setUpdatingId(null);
      setEditingId(null);
    }
  }

  async function playAudio(item: HistoryItem) {
    if (audioUrls[item.id]) {
      setExpandedAudioId(expandedAudioId === item.id ? null : item.id);
      return;
    }
    setAudioLoadingId(item.id);
    try {
      const blob = await historyAPI.fetchAudio(item.id);
      const url = URL.createObjectURL(blob);
      audioUrlsRef.current[item.id] = url;
      setAudioUrls((prev) => ({ ...prev, [item.id]: url }));
      setExpandedAudioId(item.id);
    } catch {
      showToast({ message: "Failed to load audio", type: "error" });
    } finally {
      setAudioLoadingId(null);
    }
  }

  function renderBadge(item: HistoryItem) {
    if (item.activity_type === "transcription") {
      return <span className="badge badge-blue">STT</span>;
    }
    return <span className="badge badge-purple">Translation</span>;
  }

  function renderEngine(item: HistoryItem) {
    const engine = item.engine || "—";
    return <span className="badge badge-slate text-[10px]">{engine}</span>;
  }

  function renderDisplayTitle(item: HistoryItem) {
    if (editingId === item.id) {
      return (
        <span className="flex items-center gap-1.5 min-w-0 flex-1">
          <input
            autoFocus
            value={draftTitle}
            onChange={(e) => setDraftTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") saveTitle(item.id);
              if (e.key === "Escape") setEditingId(null);
            }}
            onBlur={() => saveTitle(item.id)}
            className="input-field py-1 text-sm"
            placeholder="Untitled"
          />
          <button onClick={() => saveTitle(item.id)} className="p-1 text-emerald-500" aria-label="Save title">
            <Check className="w-4 h-4" />
          </button>
        </span>
      );
    }
    return (
      <span className="text-sm font-semibold text-foreground truncate">
        {item.title || (item.activity_type === "transcription" ? "Speech-to-text" : "Translation")}
      </span>
    );
  }

  const filterTabs: { key: FilterTab; label: string; icon: React.ReactNode }[] = [
    { key: "all", label: "All", icon: <Clock size={14} /> },
    { key: "stt", label: "Speech-to-Text", icon: <Mic size={14} /> },
    { key: "translation", label: "Translations", icon: <Languages size={14} /> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">History</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCorrections}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-secondary hover:bg-slate-100 dark:hover:bg-white/5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Export your corrections as training data (JSON)"
          >
            {exporting ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {exporting ? "Exporting..." : "Export Corrections"}
          </button>
          <span className="text-sm text-muted">{totalItems} items</span>
        </div>
      </div>

      <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-white/5 rounded-xl w-fit">
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all ${
              filter === tab.key ? "tab-active" : "tab-inactive"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search activities..."
          className="input-field pl-9"
        />
      </div>

      {loading ? (
        <div className="divide-y divide-border">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted">
          <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-white/5 flex items-center justify-center mb-4">
            <Zap size={28} className="text-slate-300 dark:text-slate-600" />
          </div>
          <p className="text-sm font-medium text-foreground">No activity yet</p>
          <p className="text-xs text-muted mt-1">
            Start translating or transcribing to see your history
          </p>
        </div>
      ) : (
        <div className="divide-y divide-border border border-border rounded-xl overflow-hidden">
          {items.map((item) => (
            <div
              key={item.id}
              className={`px-4 py-3.5 history-row transition-colors group cursor-pointer hover:bg-muted/30 ${expandedItemId === item.id ? "bg-muted/20" : ""}`}
              onClick={() => setExpandedItemId(expandedItemId === item.id ? null : item.id)}
            >
              <div className="flex items-start gap-3">
                {renderBadge(item)}

                <div className="min-w-0 flex-1">
                  {/* Title / rename row */}
                  <div className="flex items-center gap-2 mb-1">
                    {item.pinned && <Pin size={13} className="text-amber-500 shrink-0 fill-amber-500" />}
                    {renderDisplayTitle(item)}
                  </div>

                  {/* Meta row */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs text-muted">{relativeTime(item.created_at)}</span>
                    {renderEngine(item)}
                    {item.original_filename && item.audio_filename && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 dark:text-slate-500 truncate max-w-[160px]">
                        <Headphones size={10} className="shrink-0" />
                        {item.original_filename}
                      </span>
                    )}
                  </div>

                  {/* Body */}
                  <p className={`text-sm text-foreground ${expandedItemId === item.id ? "whitespace-pre-wrap" : "truncate"}`}>{item.final_text}</p>
                  {item.activity_type === "translation" && item.translation && (
                    <p className={`text-xs text-muted mt-0.5 ${expandedItemId === item.id ? "whitespace-pre-wrap" : "truncate"}`}>→ {item.translation}</p>
                  )}

                  {/* Audio player */}
                  {expandedAudioId === item.id && audioUrls[item.id] && (
                    <div className="mt-2">
                      <audio controls src={audioUrls[item.id]} className="w-full" />
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-0.5 shrink-0" onClick={(e) => e.stopPropagation()}>
                  {item.has_audio && (
                    <button
                      onClick={() => playAudio(item)}
                      disabled={audioLoadingId === item.id}
                      className="p-1.5 rounded-lg text-muted hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-colors disabled:opacity-50"
                      title={item.activity_type === "transcription" ? "Replay audio" : "Play audio"}
                    >
                      {audioLoadingId === item.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : expandedAudioId === item.id ? (
                        <X size={14} />
                      ) : (
                        <Play size={14} />
                      )}
                    </button>
                  )}

                  {item.has_audio && item.activity_type === "transcription" && (
                    <button
                      onClick={() => setRedoItem(item)}
                      disabled={updatingId === item.id}
                      className="p-1.5 rounded-lg text-muted hover:text-purple-600 dark:hover:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-500/10 transition-colors disabled:opacity-50"
                      title="Re-transcribe with a different engine"
                    >
                      <RefreshCw size={14} />
                    </button>
                  )}

                  {(item.final_text || item.raw_text) && (
                    <button
                      onClick={() => setRetranslateItem(item)}
                      disabled={updatingId === item.id}
                      className="p-1.5 rounded-lg text-muted hover:text-purple-600 dark:hover:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-500/10 transition-colors disabled:opacity-50"
                      title="Re-translate"
                    >
                      <ArrowRightLeft size={14} />
                    </button>
                  )}

                  <button
                    onClick={() => { setDraftTitle(item.title || ""); setEditingId(item.id); }}
                    disabled={updatingId === item.id}
                    className="p-1.5 rounded-lg text-muted hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-500/10 transition-colors disabled:opacity-50"
                    title="Rename"
                  >
                    <Pencil size={14} />
                  </button>

                  <button
                    onClick={() => togglePin(item)}
                    disabled={updatingId === item.id}
                    className={`p-1.5 rounded-lg transition-all ${
                      item.pinned
                        ? "text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-500/10"
                        : "text-muted opacity-0 group-hover:opacity-100 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-500/10"
                    }`}
                    title={item.pinned ? "Unpin" : "Pin to top"}
                  >
                    <Pin size={14} />
                  </button>

                  <button
                    onClick={() => handleDelete(item.id)}
                    disabled={deletingId === item.id}
                    className={`p-1.5 rounded-lg transition-all ${
                      confirmDeleteId === item.id
                        ? "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400"
                        : "text-muted opacity-0 group-hover:opacity-100 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10"
                    }`}
                    title={confirmDeleteId === item.id ? "Click again to confirm" : "Delete"}
                  >
                    {deletingId === item.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-secondary pagination-btn rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft size={14} />
            Previous
          </button>
          <span className="text-sm text-muted">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-secondary pagination-btn rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      {redoItem && (
        <RedoModal
          item={redoItem}
          onClose={() => setRedoItem(null)}
          onDone={(result) => {
            setRedoItem(null);
            setExpandedAudioId(null);
            showToast({ message: "Re-transcription complete", type: "success" });
            fetchHistory();
          }}
          onError={(msg) => {
            setRedoItem(null);
            showToast({ message: msg, type: "error" });
          }}
          showToast={showToast}
        />
      )}

      {retranslateItem && (
        <RetranslateModal
          item={retranslateItem}
          onClose={() => setRetranslateItem(null)}
          onDone={(result) => {
            setRetranslateItem(null);
            showToast({ message: "Translation saved to history", type: "success" });
            fetchHistory();
          }}
          onError={(msg) => {
            setRetranslateItem(null);
            showToast({ message: msg, type: "error" });
          }}
        />
      )}
    </div>
  );
}