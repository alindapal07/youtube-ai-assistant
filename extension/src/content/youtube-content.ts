import { MESSAGE_TYPES, VideoChangedPayload } from "../shared/messages";

(() => {
  let activeVideoId: string | null = null;
  let activeTitle: string | null = null;
  let titlePollInterval: ReturnType<typeof setInterval> | null = null;

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

  function getDOMVideoTitle(): string | null {
    // 1. Try YouTube's specific watch-metadata title element
    const titleEl = document.querySelector<HTMLElement>(
      "ytd-watch-metadata #title h1 yt-formatted-string, h1.ytd-watch-metadata yt-formatted-string, #title h1 yt-formatted-string"
    );
    if (titleEl && titleEl.textContent && titleEl.textContent.trim()) {
      return titleEl.textContent.trim();
    }

    // 2. Try document title if it does not equal generic "YouTube"
    if (document.title && !document.title.startsWith("YouTube") && document.title.includes(" - YouTube")) {
      return document.title.replace(" - YouTube", "").trim();
    }

    // 3. Try meta tag
    const metaTitle = document.querySelector('meta[name="title"]')?.getAttribute("content");
    if (metaTitle && metaTitle.trim()) {
      return metaTitle.trim();
    }

    return null;
  }

  function sendVideoChange(videoId: string, url: string, title: string | null) {
    const payload: VideoChangedPayload = {
      videoId,
      url,
      title: title || undefined,
    };

    try {
      chrome.runtime.sendMessage(
        {
          type: MESSAGE_TYPES.VIDEO_CHANGED,
          payload,
        },
        () => {
          if (chrome.runtime.lastError) {
            // Extension context may have been reloaded; safe to ignore
          }
        }
      );
    } catch (err) {
      console.debug("Failed to notify video change:", err);
    }
  }

  function watchTitleForVideo(targetVideoId: string) {
    if (titlePollInterval) {
      clearInterval(titlePollInterval);
      titlePollInterval = null;
    }

    let pollCount = 0;
    // Check every 250ms for up to 5 seconds to catch YouTube's async title rendering
    titlePollInterval = setInterval(() => {
      pollCount++;
      const currentId = extractVideoId(window.location.href);

      // If user navigated away to another video, stop this poller
      if (currentId !== targetVideoId || pollCount > 20) {
        if (titlePollInterval) clearInterval(titlePollInterval);
        titlePollInterval = null;
        return;
      }

      const latestTitle = getDOMVideoTitle();
      if (latestTitle && latestTitle !== activeTitle) {
        activeTitle = latestTitle;
        sendVideoChange(targetVideoId, window.location.href, activeTitle);
      }
    }, 250);
  }

  function checkNavigation() {
    const currentUrl = window.location.href;
    const currentVideoId = extractVideoId(currentUrl);

    if (currentVideoId && currentVideoId !== activeVideoId) {
      activeVideoId = currentVideoId;
      activeTitle = null; // Reset title immediately so old video title never persists

      const initialTitle = getDOMVideoTitle();
      activeTitle = initialTitle;

      sendVideoChange(currentVideoId, currentUrl, initialTitle);

      // Actively poll to capture the title once YouTube finishes rendering the new video component
      watchTitleForVideo(currentVideoId);
    } else if (!currentVideoId && activeVideoId !== null) {
      activeVideoId = null;
      activeTitle = null;
      if (titlePollInterval) clearInterval(titlePollInterval);
    }
  }

  // 1. Initial check when script loads
  checkNavigation();

  // 2. YouTube custom SPA events
  window.addEventListener("yt-navigate-finish", () => {
    checkNavigation();
    setTimeout(checkNavigation, 200);
    setTimeout(checkNavigation, 600);
  });

  // 3. Browser navigation popstate
  window.addEventListener("popstate", () => {
    setTimeout(checkNavigation, 100);
  });

  // 4. MutationObserver on document title and head
  const titleObserver = new MutationObserver(() => {
    if (activeVideoId) {
      const latestTitle = getDOMVideoTitle();
      if (latestTitle && latestTitle !== activeTitle) {
        activeTitle = latestTitle;
        sendVideoChange(activeVideoId, window.location.href, activeTitle);
      }
    }
  });

  titleObserver.observe(document.querySelector("title") || document.head, {
    subtree: true,
    characterData: true,
    childList: true,
  });
})();
