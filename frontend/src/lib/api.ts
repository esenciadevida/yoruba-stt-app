import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      const url = err.config?.url || "";
      const isAuthEndpoint = url.includes("/api/auth/login") || url.includes("/api/auth/register") || url.includes("/api/auth/admin/login");
      if (!isAuthEndpoint) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/auth";
      }
    }
    return Promise.reject(err);
  }
);

export const adminApi = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

adminApi.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("admin_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

adminApi.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      const isLoginPage = window.location.pathname === "/admin/login";
      if (!isLoginPage) {
        localStorage.removeItem("admin_token");
        localStorage.removeItem("admin_user");
        window.location.href = "/admin/login";
      }
    }
    return Promise.reject(err);
  }
);

export interface User {
  id: number;
  username: string;
  email: string | null;
  is_admin: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface WordConfidence {
  word: string;
  confidence: number;
  start?: number;
  end?: number;
}

export interface AudioQuality {
  duration_sec: number;
  rms_energy: number;
  is_silent: boolean;
  is_clipped: boolean;
  warnings: string[];
}

export interface TranscribeResult {
  raw_text: string;
  final_text: string;
  confidence: number | null;
  word_confidences: WordConfidence[];
  quality: AudioQuality | null;
  id: number;
  created_at: string;
  detected_language?: string;
  engine?: string;
  code_switched?: boolean;
}

export interface CorrectionResult {
  id: number;
  original_text: string;
  corrected_text: string;
  created_at: string;
}

export interface TranslateResult {
  source_text: string;
  translated_text: string;
  detected_language: string;
  target_language: string;
  engine: string;
  quality?: string;
  code_switched?: boolean;
}

export type ActivityType = "transcription" | "translation";

export interface HistoryItem {
  id: number;
  activity_type: ActivityType;
  raw_text: string | null;
  final_text: string | null;
  translation: string | null;
  source_language: string | null;
  target_language: string | null;
  engine: string | null;
  audio_filename: string | null;
  original_filename: string | null;
  title: string | null;
  pinned: boolean;
  has_audio: boolean;
  created_at: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface UserStats {
  total_transcriptions: number;
  total_translations: number;
  total_words_translated: number;
  account_created: string;
}

export const authAPI = {
  register: (username: string, password: string, email?: string) =>
    api.post<AuthResponse>("/api/auth/register", { username, password, email }),
  login: (username: string, password: string) =>
    api.post<AuthResponse>("/api/auth/login", { username, password }),
  adminLogin: (username: string, password: string) =>
    adminApi.post<AuthResponse>("/api/auth/admin/login", { username, password }),
  me: () => api.get<User>("/api/auth/me"),
  stats: () => api.get<UserStats>("/api/auth/stats"),
  updateProfile: (username: string, email: string | null) =>
    api.put<User>("/api/auth/profile", { username, email }),
  changePassword: (current_password: string, new_password: string) =>
    api.put("/api/auth/password", { current_password, new_password }),
};

export const transcribeAPI = {
  transcribe: (audioBlob: Blob, filename: string, language: string = "yo") => {
    const formData = new FormData();
    formData.append("audio", audioBlob, filename);
    formData.append("language", language);
    return api.post<TranscribeResult>("/api/transcribe", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  draftOnly: (audioBlob: Blob, filename: string, language: string = "yo") => {
    const formData = new FormData();
    formData.append("audio", audioBlob, filename);
    formData.append("language", language);
    formData.append("draft_only", "true");
    return api.post<TranscribeResult>("/api/transcribe", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  polish: (text: string, language: string = "yo") =>
    api.post<{ text: string }>(
      "/api/transcribe/polish",
      { text, language },
      { timeout: 120000 }
    ),
};

export const translateAPI = {
  translate: (text: string, direction: string = "auto") =>
    api.post<TranslateResult>("/api/translate", { text, direction }, { timeout: 120000 }),
  translateStream: (text: string, direction: string = "auto", onToken: (token: string) => void, onDone: (result: any) => void, onError: (error: string) => void, signal?: AbortSignal) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    fetch(`${API_BASE}/api/translate/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ text, direction }),
      signal,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Streaming failed" }));
        onError(err.detail || "Streaming failed");
        return;
      }
      const reader = res.body?.getReader();
      if (!reader) { onError("No response stream"); return; }
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) { onError(data.error); return; }
            if (data.done) { onDone(data); return; }
            if (data.token) onToken(data.token);
          } catch {}
        }
      }
    }).catch((err) => {
      if (err?.name === "AbortError") {
        onError("canceled");
        return;
      }
      onError(err.message || "Network error");
    });
  },
};

export const correctionAPI = {
  save: (transcription_id: number, corrected_text: string) =>
    api.post<CorrectionResult>("/api/corrections", { transcription_id, corrected_text }),
  export: () => api.get<{ total: number; corrections: { input: string; target: string }[] }>("/api/corrections/export"),
};

export const ttsAPI = {
  synthesize: (text: string, lang: string = "yo") => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    return fetch(`${API_BASE}/api/tts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ text, lang }),
    }).then((res) => {
      if (!res.ok) throw new Error("TTS failed");
      return res.blob();
    });
  },
};

export const historyAPI = {
  list: (page: number = 1, perPage: number = 20, activityType?: ActivityType, search?: string) => {
    const params: Record<string, any> = { page, per_page: perPage };
    if (activityType) params.activity_type = activityType;
    if (search) params.search = search;
    return api.get<HistoryResponse>("/api/history", { params });
  },
  delete: (id: number) => api.delete(`/api/history/${id}`),
  update: (id: number, data: { title?: string | null; pinned?: boolean }) =>
    api.patch<HistoryItem>(`/api/history/${id}`, data),
  retranscribe: (id: number, language: string = "auto", preferredEngine: string = "auto") => {
    const formData = new FormData();
    formData.append("language", language);
    formData.append("preferred_engine", preferredEngine);
    return api.post<TranscribeResult>(`/api/history/${id}/retranscribe`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  retranslate: (id: number, direction: string = "auto") =>
    api.post<TranslateResult>(
      `/api/history/${id}/retranslate`,
      { direction },
      { timeout: 120000 }
    ),
  fetchAudio: async (id: number): Promise<Blob> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const res = await fetch(`${API_BASE}/api/history/${id}/audio`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("Failed to load audio");
    return res.blob();
  },
};

export interface AdminUserItem {
  id: number;
  username: string;
  email: string | null;
  is_admin: boolean;
  created_at: string;
  transcription_count: number;
  translation_count: number;
  last_active: string | null;
}

export interface AdminUserDetail extends AdminUserItem {
  total_words_transcribed: number;
  total_words_translated: number;
  recent_activity: AdminActivityItem[];
}

export interface AdminCreateUser {
  username: string;
  password: string;
  email?: string;
  is_admin?: boolean;
}

export interface AdminUpdateUser {
  username?: string;
  email?: string;
  password?: string;
  is_admin?: boolean;
}

export interface AdminStats {
  total_users: number;
  total_transcriptions: number;
  total_translations: number;
  active_users_7d: number;
  recent_signups: number;
  total_words_transcribed: number;
  total_words_translated: number;
  daily_activity: { date: string; count: number }[];
}

export interface AdminActivityItem {
  id: number;
  user: string;
  user_id: number;
  activity_type: string;
  summary: string;
  engine: string | null;
  created_at: string;
}

export interface AdminSystemHealth {
  status: string;
  db_connected: boolean;
  asr_model_loaded: boolean;
  translation_engine: string;
  total_storage_mb: number;
  uptime_seconds: number;
}

export const adminAPI = {
  stats: () => adminApi.get<AdminStats>("/api/admin/stats"),
  health: () => adminApi.get<AdminSystemHealth>("/api/admin/health"),
  users: (page = 1, search = "", role?: string) => {
    const params: Record<string, any> = { page, per_page: 20 };
    if (search) params.search = search;
    if (role) params.role = role;
    return adminApi.get<{ items: AdminUserItem[]; total: number }>("/api/admin/users", { params });
  },
  getUser: (id: number) => adminApi.get<AdminUserDetail>(`/api/admin/users/${id}`),
  createUser: (data: AdminCreateUser) => adminApi.post<AdminUserItem>("/api/admin/users", data),
  updateUser: (id: number, data: AdminUpdateUser) => adminApi.put<AdminUserItem>(`/api/admin/users/${id}`, data),
  toggleRole: (id: number) => adminApi.put<{ is_admin: boolean }>(`/api/admin/users/${id}/role`),
  deleteUser: (id: number) => adminApi.delete(`/api/admin/users/${id}`),
  activity: (page = 1, activityType?: string, userId?: number) => {
    const params: Record<string, any> = { page, per_page: 30 };
    if (activityType) params.activity_type = activityType;
    if (userId) params.user_id = userId;
    return adminApi.get<{ items: AdminActivityItem[]; total: number }>("/api/admin/activity", { params });
  },
  auditLogs: (page = 1) =>
    adminApi.get<{ items: AuditLogItem[]; total: number }>("/api/admin/audit", { params: { page, per_page: 30 } }),
};

export interface AuditLogItem {
  id: number;
  admin_id: number;
  admin_username: string;
  action: string;
  target_type: string;
  target_id: number | null;
  detail: string;
  ip_address: string | null;
  created_at: string;
}

export default api;
