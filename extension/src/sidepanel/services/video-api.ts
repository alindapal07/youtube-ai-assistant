import { apiClient } from "./api-client";
import { VideoInfoResponse, VideoProcessResponse } from "../types/video";

export const videoApi = {
  async getVideoInfo(videoId: string, signal?: AbortSignal): Promise<VideoInfoResponse> {
    return apiClient.request<VideoInfoResponse>(`/videos/${encodeURIComponent(videoId)}`, {
      method: "GET",
      signal,
    });
  },

  async processVideo(
    videoId: string,
    language: string = "en",
    signal?: AbortSignal
  ): Promise<VideoProcessResponse> {
    return apiClient.request<VideoProcessResponse>("/videos/process", {
      method: "POST",
      body: JSON.stringify({ video_id: videoId, language }),
      signal,
      timeoutMs: 180000, // Processing long transcripts with chunk embeddings
    });
  },
};

