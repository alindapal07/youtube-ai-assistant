import { useEffect, useState } from "react";
import { MESSAGE_TYPES, ExtensionMessage, VideoChangedPayload } from "../../shared/messages";
import { STORAGE_KEYS } from "../../shared/constants";

export interface CurrentVideoState {
  videoId: string | null;
  url: string | null;
  title: string | null;
  isLoading: boolean;
}

export function useCurrentVideo() {
  const [videoState, setVideoState] = useState<CurrentVideoState>({
    videoId: null,
    url: null,
    title: null,
    isLoading: true,
  });

  useEffect(() => {
    let isMounted = true;

    // 1. Initial detection: Check storage, then query active tab
    const detectCurrentVideo = async () => {
      try {
        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
          const res = await chrome.storage.local.get([STORAGE_KEYS.CURRENT_VIDEO]);
          const stored = res[STORAGE_KEYS.CURRENT_VIDEO] as VideoChangedPayload | undefined;
          if (stored && stored.videoId && isMounted) {
            setVideoState({
              videoId: stored.videoId,
              url: stored.url,
              title: stored.title || null,
              isLoading: false,
            });
            return;
          }
        }

        // Query active tab directly if chrome.tabs is available
        if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
          const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
          if (tab && tab.url && isMounted) {
            const vid = extractVideoId(tab.url);
            setVideoState({
              videoId: vid,
              url: tab.url,
              title: tab.title || null,
              isLoading: false,
            });
            return;
          }
        }
      } catch (err) {
        console.warn("Error detecting video on mount:", err);
      }

      if (isMounted) {
        setVideoState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    detectCurrentVideo();

    // 2. Listen for runtime messages from content script or background worker
    const messageListener = (message: ExtensionMessage) => {
      if (!isMounted || !message) return;

      if (message.type === MESSAGE_TYPES.VIDEO_CHANGED) {
        const payload = message.payload as VideoChangedPayload;
        if (payload && payload.videoId) {
          setVideoState((prev) => {
            if (prev.videoId === payload.videoId) {
              return {
                ...prev,
                title: payload.title || prev.title,
                url: payload.url,
                isLoading: false,
              };
            }
            return {
              videoId: payload.videoId,
              url: payload.url,
              title: payload.title || null,
              isLoading: false,
            };
          });
        }
      }
    };

    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
      chrome.runtime.onMessage.addListener(messageListener);
    }

    return () => {
      isMounted = false;
      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
        chrome.runtime.onMessage.removeListener(messageListener);
      }
    };
  }, []);

  return videoState;
}

function extractVideoId(urlStr: string): string | null {
  try {
    const url = new URL(urlStr);
    if (url.hostname.includes("youtube.com")) {
      if (url.pathname === "/watch") {
        return url.searchParams.get("v");
      }
      if (url.pathname.startsWith("/shorts/")) {
        const parts = url.pathname.split("/");
        return parts[2] || null;
      }
    } else if (url.hostname === "youtu.be") {
      return url.pathname.slice(1) || null;
    }
  } catch {
    return null;
  }
  return null;
}

