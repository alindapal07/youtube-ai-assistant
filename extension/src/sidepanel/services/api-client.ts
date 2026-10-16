import { APP_LIMITS, DEFAULT_API_BASE_URL, STORAGE_KEYS } from "../../shared/constants";
import { ApiError } from "../types/api";

export class ApiClientError extends Error {
  public errorCode: string;
  public status: number;
  public details?: unknown;

  constructor(message: string, errorCode: string = "API_ERROR", status: number = 500, details?: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.errorCode = errorCode;
    this.status = status;
    this.details = details;
  }
}

class ApiClient {
  private baseUrl: string = DEFAULT_API_BASE_URL;

  constructor() {
    this.loadBaseUrl();
  }

  private async loadBaseUrl() {
    try {
      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        const result = await chrome.storage.local.get([STORAGE_KEYS.API_BASE_URL]);
        if (result[STORAGE_KEYS.API_BASE_URL]) {
          this.baseUrl = result[STORAGE_KEYS.API_BASE_URL];
        }
      }
    } catch {
      // Fallback to default
    }
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, "");
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ [STORAGE_KEYS.API_BASE_URL]: this.baseUrl }).catch(() => {});
    }
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit & { signal?: AbortSignal; timeoutMs?: number } = {}
  ): Promise<T> {
    const { timeoutMs = APP_LIMITS.REQUEST_TIMEOUT_MS, signal: externalSignal, ...fetchOptions } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // Chain external abort signal if supplied
    if (externalSignal) {
      externalSignal.addEventListener("abort", () => {
        controller.abort();
        clearTimeout(timeoutId);
      });
    }

    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = `${this.baseUrl}${cleanEndpoint}`;

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(fetchOptions.headers || {}),
        },
      });

      clearTimeout(timeoutId);

      const contentType = response.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");

      if (!response.ok) {
        if (isJson) {
          const errData = (await response.json()) as ApiError;
          throw new ApiClientError(
            errData.message || `Request failed with status ${response.status}`,
            errData.error_code || "SERVER_ERROR",
            response.status,
            errData.details
          );
        } else {
          const errText = await response.text();
          throw new ApiClientError(
            errText || `Server returned error status ${response.status}`,
            "HTTP_ERROR",
            response.status
          );
        }
      }

      if (isJson) {
        return (await response.json()) as T;
      }
      return (await response.text()) as unknown as T;
    } catch (err: unknown) {
      clearTimeout(timeoutId);

      if (err instanceof ApiClientError) {
        throw err;
      }

      if (err instanceof DOMException && err.name === "AbortError") {
        throw new ApiClientError("Request timed out or was cancelled.", "REQUEST_TIMEOUT", 408);
      }

      if (err instanceof TypeError && err.message.includes("fetch")) {
        throw new ApiClientError(
          "Could not connect to YouTube AI Assistant backend. Please check that the server is running on http://127.0.0.1:8000.",
          "NETWORK_ERROR",
          0
        );
      }

      throw new ApiClientError(
        err instanceof Error ? err.message : "An unexpected network error occurred.",
        "UNKNOWN_ERROR",
        500
      );
    }
  }
}

export const apiClient = new ApiClient();

