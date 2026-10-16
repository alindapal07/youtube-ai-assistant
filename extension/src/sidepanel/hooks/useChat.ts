import { useCallback, useEffect, useRef, useState } from "react";
import { chatApi } from "../services/chat-api";
import { insightsApi } from "../services/insights-api";
import { ChatMessage } from "../types/chat";

export function useChat(videoId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate or retrieve session ID for this video
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`);

  const activeVideoIdRef = useRef<string | null>(videoId);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Clear messages or update ref when videoId changes
  useEffect(() => {
    activeVideoIdRef.current = videoId;
    setMessages([]);
    setError(null);
    setIsLoading(false);

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, [videoId]);

  const sendMessage = useCallback(
    async (questionText: string) => {
      const cleanQuestion = questionText.trim();
      const currentVideoId = activeVideoIdRef.current;

      if (!cleanQuestion || !currentVideoId || isLoading) {
        return;
      }

      setError(null);
      setIsLoading(true);

      const userMsgId = `user_${Date.now()}`;
      const userMessage: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: cleanQuestion,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await chatApi.askQuestion(
          currentVideoId,
          sessionId,
          cleanQuestion,
          controller.signal
        );

        // Discard response if video changed during in-flight request
        if (activeVideoIdRef.current !== currentVideoId) return;

        const assistantMsgId = `assistant_${Date.now()}`;
        const assistantMessage: ChatMessage = {
          id: assistantMsgId,
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err: unknown) {
        if (activeVideoIdRef.current !== currentVideoId) return;
        if (err instanceof Error && err.name === "AbortError") return;

        const errorMsg = err instanceof Error ? err.message : "Failed to obtain response.";
        setError(errorMsg);

        // Also add error message into chat stream for clear visibility
        setMessages((prev) => [
          ...prev,
          {
            id: `err_${Date.now()}`,
            role: "assistant",
            content: `Error: ${errorMsg}`,
            timestamp: new Date().toISOString(),
            error: true,
          },
        ]);
      } finally {
        if (activeVideoIdRef.current === currentVideoId) {
          setIsLoading(false);
        }
      }
    },
    [isLoading, sessionId]
  );

  const requestSummary = useCallback(async () => {
    const currentVideoId = activeVideoIdRef.current;
    if (!currentVideoId || isLoading) return;

    setIsLoading(true);
    setError(null);

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: "Please provide a comprehensive summary of this video.",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const res = await insightsApi.getSummary(currentVideoId);
      if (activeVideoIdRef.current !== currentVideoId) return;

      setMessages((prev) => [
        ...prev,
        {
          id: `asst_${Date.now()}`,
          role: "assistant",
          content: res.summary,
          sources: res.sources,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: unknown) {
      if (activeVideoIdRef.current !== currentVideoId) return;
      const msg = err instanceof Error ? err.message : "Failed to generate video summary.";
      setError(msg);
    } finally {
      if (activeVideoIdRef.current === currentVideoId) {
        setIsLoading(false);
      }
    }
  }, [isLoading]);

  const requestNotes = useCallback(async () => {
    const currentVideoId = activeVideoIdRef.current;
    if (!currentVideoId || isLoading) return;

    setIsLoading(true);
    setError(null);

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: "Please generate structured study notes and key takeaways for this video.",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const res = await insightsApi.getStudyNotes(currentVideoId);
      if (activeVideoIdRef.current !== currentVideoId) return;

      const fullContent = `${res.notes}\n\n### Key Takeaways\n${res.key_takeaways.map((t) => `• ${t}`).join("\n")}`;

      setMessages((prev) => [
        ...prev,
        {
          id: `asst_${Date.now()}`,
          role: "assistant",
          content: fullContent,
          sources: res.sources,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: unknown) {
      if (activeVideoIdRef.current !== currentVideoId) return;
      const msg = err instanceof Error ? err.message : "Failed to generate study notes.";
      setError(msg);
    } finally {
      if (activeVideoIdRef.current === currentVideoId) {
        setIsLoading(false);
      }
    }
  }, [isLoading]);

  const requestQuestions = useCallback(async () => {
    const currentVideoId = activeVideoIdRef.current;
    if (!currentVideoId || isLoading) return;

    setIsLoading(true);
    setError(null);

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: "Please generate technical interview / revision questions based on this video.",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const res = await insightsApi.getInterviewQuestions(currentVideoId);
      if (activeVideoIdRef.current !== currentVideoId) return;

      const formattedQuestions = res.questions.join("\n\n---\n\n");

      setMessages((prev) => [
        ...prev,
        {
          id: `asst_${Date.now()}`,
          role: "assistant",
          content: formattedQuestions,
          sources: res.sources,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: unknown) {
      if (activeVideoIdRef.current !== currentVideoId) return;
      const msg = err instanceof Error ? err.message : "Failed to generate interview questions.";
      setError(msg);
    } finally {
      if (activeVideoIdRef.current === currentVideoId) {
        setIsLoading(false);
      }
    }
  }, [isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    if (activeVideoIdRef.current) {
      chatApi.clearHistory(activeVideoIdRef.current, sessionId).catch(() => {});
    }
  }, [sessionId]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    requestSummary,
    requestNotes,
    requestQuestions,
    clearMessages,
  };
}

