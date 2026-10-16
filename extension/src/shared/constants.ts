export const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

export const STORAGE_KEYS = {
  CURRENT_VIDEO: "yt_ai_current_video",
  API_BASE_URL: "yt_ai_api_base_url",
  ACTIVE_SESSION: "yt_ai_session_id",
} as const;

export const APP_LIMITS = {
  MAX_QUESTION_LENGTH: 1000,
  REQUEST_TIMEOUT_MS: 120000,
} as const;

