import { apiClient } from "./api-client";
import { ChatResponse, ChatMessage } from "../types/chat";

export const chatApi = {
  async askQuestion(
    videoId: string,
    sessionId: string,
    question: string,
    signal?: AbortSignal
  ): Promise<ChatResponse> {
    return apiClient.request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({
        video_id: videoId,
        session_id: sessionId,
        question,
      }),
      signal,
      timeoutMs: 45000,
    });
  },

  async getHistory(
    videoId: string,
    sessionId: string,
    signal?: AbortSignal
  ): Promise<{ messages: ChatMessage[] }> {
    return apiClient.request<{ messages: ChatMessage[] }>(
      `/chat/history/${encodeURIComponent(sessionId)}?video_id=${encodeURIComponent(videoId)}`,
      {
        method: "GET",
        signal,
      }
    );
  },

  async clearHistory(videoId: string, sessionId: string): Promise<{ success: boolean }> {
    return apiClient.request<{ success: boolean }>(
      `/chat/history/${encodeURIComponent(sessionId)}?video_id=${encodeURIComponent(videoId)}`,
      {
        method: "DELETE",
      }
    );
  },
};

