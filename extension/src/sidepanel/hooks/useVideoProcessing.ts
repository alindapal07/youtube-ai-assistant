import { useCallback, useEffect, useRef, useState } from "react";
import { videoApi } from "../services/video-api";

export type ProcessingStatus = "idle" | "checking" | "processing" | "ready" | "error";

export interface VideoProcessingState {
  status: ProcessingStatus;
  indexed: boolean;
  chunksCount: number | null;
  error: string | null;
  language: string;
  title: string | null;
}

export function useVideoProcessing(videoId: string | null) {
  const [state, setState] = useState<VideoProcessingState>({
    status: "idle",
    indexed: false,
    chunksCount: null,
    error: null,
    language: "en",
    title: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const activeVideoIdRef = useRef<string | null>(videoId);

  // Keep ref up to date
  useEffect(() => {
    activeVideoIdRef.current = videoId;
  }, [videoId]);

  const checkIndexStatus = useCallback(async (targetVideoId: string) => {
    // Abort previous in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setState((prev) => ({
      ...prev,
      status: "checking",
      error: null,
      title: null,
    }));

    try {
      const info = await videoApi.getVideoInfo(targetVideoId, controller.signal);

      // Verify response belongs to currently active video
      if (activeVideoIdRef.current !== targetVideoId) return;

      const videoTitle = info.title || info.metadata?.title || null;

      if (info.indexed) {
        setState({
          status: "ready",
          indexed: true,
          chunksCount: info.chunks_count,
          error: null,
          language: info.metadata?.language || "en",
          title: videoTitle,
        });
      } else {
        setState({
          status: "idle",
          indexed: false,
          chunksCount: null,
          error: null,
          language: "en",
          title: videoTitle,
        });
      }
    } catch (err: unknown) {
      if (activeVideoIdRef.current !== targetVideoId) return;
      if (err instanceof Error && err.name === "AbortError") return;

      setState({
        status: "idle",
        indexed: false,
        chunksCount: null,
        error: null,
        language: "en",
        title: null,
      });
    }
  }, []);

  const processVideo = useCallback(
    async (language: string = "en") => {
      const targetVideoId = activeVideoIdRef.current;
      if (!targetVideoId) return;

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setState((prev) => ({
        ...prev,
        status: "processing",
        error: null,
        language,
      }));

      try {
        const result = await videoApi.processVideo(targetVideoId, language, controller.signal);

        if (activeVideoIdRef.current !== targetVideoId) return;

        setState((prev) => ({
          status: "ready",
          indexed: true,
          chunksCount: result.chunks_created,
          error: null,
          language,
          title: result.title || prev.title,
        }));
      } catch (err: unknown) {
        if (activeVideoIdRef.current !== targetVideoId) return;
        if (err instanceof Error && err.name === "AbortError") return;

        const message = err instanceof Error ? err.message : "Failed to process video transcript.";
        setState((prev) => ({
          ...prev,
          status: "error",
          error: message,
        }));
      }
    },
    []
  );

  // Automatically check video status when videoId changes
  useEffect(() => {
    if (videoId) {
      checkIndexStatus(videoId);
    } else {
      setState({
        status: "idle",
        indexed: false,
        chunksCount: null,
        error: null,
        language: "en",
        title: null,
      });
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [videoId, checkIndexStatus]);

  return {
    ...state,
    processVideo,
    retry: () => processVideo(state.language),
  };
}
