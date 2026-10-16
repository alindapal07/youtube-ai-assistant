import { MESSAGE_TYPES, ExtensionMessage, VideoChangedPayload } from "../shared/messages";
import { STORAGE_KEYS } from "../shared/constants";

// Manifest V3: Register listeners synchronously at top level

// 1. Enable side panel on extension icon click
chrome.runtime.onInstalled.addListener(() => {
  if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch((err) => {
      console.warn("Could not set side panel behavior:", err);
    });
  }
});

// 2. Track tab switches / activations to detect video in active tab
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab && tab.url && tab.url.includes("youtube.com")) {
      const videoId = extractVideoIdFromUrl(tab.url);
      if (videoId) {
        const payload: VideoChangedPayload = {
          videoId,
          url: tab.url,
          title: tab.title,
        };
        await chrome.storage.local.set({ [STORAGE_KEYS.CURRENT_VIDEO]: payload });
        // Notify any open side panel
        chrome.runtime.sendMessage({
          type: MESSAGE_TYPES.VIDEO_CHANGED,
          payload,
        }).catch(() => {
          // Ignore error if side panel is not currently open
        });
      }
    }
  } catch (err) {
    console.debug("Tab activation check error:", err);
  }
});

// 3. Listen for messages from content scripts and sidepanel
chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender, sendResponse) => {
  if (!message || typeof message.type !== "string") {
    return false;
  }

  if (message.type === MESSAGE_TYPES.VIDEO_CHANGED) {
    const payload = message.payload as VideoChangedPayload;
    if (payload && payload.videoId) {
      // Store current video metadata in chrome.storage for panel recovery
      chrome.storage.local.set({ [STORAGE_KEYS.CURRENT_VIDEO]: payload }).catch((err) => {
        console.warn("Failed to store current video in storage:", err);
      });

      // Relay to any open side panel or views
      chrome.runtime.sendMessage({
        type: MESSAGE_TYPES.VIDEO_CHANGED,
        payload,
      }).catch(() => {
        // No open views listening, safe to ignore
      });

      sendResponse({ received: true });
    }
    return true;
  }

  if (message.type === MESSAGE_TYPES.GET_CURRENT_VIDEO) {
    // Check chrome.storage first, fallback to active tab query
    chrome.storage.local.get([STORAGE_KEYS.CURRENT_VIDEO]).then(async (result) => {
      const stored = result[STORAGE_KEYS.CURRENT_VIDEO] as VideoChangedPayload | undefined;
      if (stored && stored.videoId) {
        sendResponse({ videoId: stored.videoId, url: stored.url, title: stored.title });
        return;
      }

      // Query active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url && tab.url.includes("youtube.com")) {
        const videoId = extractVideoIdFromUrl(tab.url);
        sendResponse({ videoId: videoId || null, url: tab.url || null, title: tab.title });
      } else {
        sendResponse({ videoId: null, url: null, title: null });
      }
    }).catch((err) => {
      console.warn("Error retrieving current video:", err);
      sendResponse({ videoId: null, url: null, title: null });
    });

    return true; // Keep channel open for async response
  }

  if (message.type === MESSAGE_TYPES.PING) {
    sendResponse({ type: MESSAGE_TYPES.PONG });
    return false;
  }

  return false;
});

function extractVideoIdFromUrl(urlStr: string): string | null {
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
      if (url.pathname.startsWith("/embed/")) {
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
