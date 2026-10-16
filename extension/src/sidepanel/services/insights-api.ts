import { apiClient } from "./api-client";
import {
  InterviewQuestionsResponse,
  StudyNotesResponse,
  VideoSummaryResponse,
} from "../types/chat";

export const insightsApi = {
  async getSummary(videoId: string, signal?: AbortSignal): Promise<VideoSummaryResponse> {
    return apiClient.request<VideoSummaryResponse>(
      `/videos/${encodeURIComponent(videoId)}/summary`,
      {
        method: "POST",
        signal,
        timeoutMs: 45000,
      }
    );
  },

  async getStudyNotes(videoId: string, signal?: AbortSignal): Promise<StudyNotesResponse> {
    return apiClient.request<StudyNotesResponse>(
      `/videos/${encodeURIComponent(videoId)}/notes`,
      {
        method: "POST",
        signal,
        timeoutMs: 45000,
      }
    );
  },

  async getInterviewQuestions(
    videoId: string,
    signal?: AbortSignal
  ): Promise<InterviewQuestionsResponse> {
    return apiClient.request<InterviewQuestionsResponse>(
      `/videos/${encodeURIComponent(videoId)}/questions`,
      {
        method: "POST",
        signal,
        timeoutMs: 45000,
      }
    );
  },
};

