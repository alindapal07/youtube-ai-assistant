# YouTube AI Assistant - Chrome Extension (Manifest V3)

A high-performance Chrome Extension built with Manifest V3, React 18, TypeScript, and Vite. Interacts with the Python FastAPI RAG backend to provide grounded AI answers and insights for YouTube videos directly in the Chrome Side Panel.

---

## Features

- **Manifest V3 Architecture**: Modern service worker, side panel API, and content scripts.
- **Real-Time Video Detection**: Automatically detects YouTube watch pages and client-side SPA navigation (`yt-navigate-finish`, `popstate`).
- **Interactive Side Panel**:
  - Displays detected video title and processing status.
  - "Process Video" action to trigger transcript chunking and FAISS indexing on the backend.
  - Grounded Chat Window with scroll-to-latest and copy answer actions.
  - Precise timestamp citation chips (e.g. `⏱ 02:15 - 02:45`) linking directly to the video section.
  - Quick action chips for **Summarize**, **Study Notes**, and **Interview Questions**.
  - Multiline text input with `Enter` to send and `Shift+Enter` for new lines.
- **Video Switch Isolation**: Automatically clears conversation and detects if newly visited videos are indexed, discarding any delayed stale network responses.

---

## Installation & Build Instructions

### 1. Install Node Dependencies

Open PowerShell in the `extension/` directory:

```powershell
cd extension
npm install
```

### 2. Build Unpacked Extension

```powershell
npm run build
```

This compiles:
- `dist/sidepanel/index.html` (React application)
- `dist/background/service-worker.js` (Extension background service worker)
- `dist/content/youtube-content.js` (YouTube SPA observer content script)
- `dist/manifest.json`
- `dist/icons/`

### 3. Load into Google Chrome

1. Open Google Chrome.
2. Navigate to `chrome://extensions`.
3. In the top-right corner, turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the `extension/dist` folder located in this project.
6. The extension **YouTube AI Assistant** will appear in your extensions list.

---

## Usage

1. Start the backend API (`uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`).
2. Open any YouTube video (for example, `https://www.youtube.com/watch?v=Gfr50f6ZBvo`).
3. Click the **YouTube AI Assistant** extension icon in your Chrome toolbar.
4. The Chrome Side Panel opens beside the video.
5. Click **Process Video** to index the transcript.
6. Ask questions or click **Summarize**, **Study Notes**, or **Interview Qs**.

