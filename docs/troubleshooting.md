# YouTube AI Assistant — Troubleshooting Guide

Common issues, diagnosis steps, and solutions.

---

## 1. Backend & Python Issues

### Issue: `GROQ_API_KEY is not configured`
- **Symptom**: Chat and insight requests return HTTP 502 with `LLM_PROVIDER_ERROR`.
- **Cause**: The `.env` file does not contain a valid `GROQ_API_KEY`.
- **Fix**:
  1. Open `backend/.env`.
  2. Set `GROQ_API_KEY=gsk_...` with an active key from [Groq Console](https://console.groq.com/keys).
  3. Restart uvicorn.

### Issue: `Transcripts are disabled for this video`
- **Symptom**: Processing returns HTTP 403 `TRANSCRIPTS_DISABLED`.
- **Cause**: The creator of the YouTube video has disabled captions/transcripts.
- **Fix**: The assistant requires video transcripts to generate grounded RAG answers. Test with a video that has closed captions enabled (such as educational lectures, podcasts, or tutorials).

### Issue: `No transcript found for video in languages: ['en']`
- **Symptom**: Processing returns HTTP 404 `TRANSCRIPT_NOT_FOUND`.
- **Cause**: The video does not provide English captions (either manual or auto-generated).
- **Fix**: Try specifying the video's native language code (e.g. `es`, `fr`, `de`) or choose an English-captioned video.

### Issue: FAISS Index Deserialization Warning
- **Symptom**: `DeprecationWarning: langchain-community is being sunset...`
- **Explanation**: This is a harmless deprecation notice from LangChain regarding upcoming community package restructuring. The backend runs FAISS CPU safely using verified `metadata.json` validation before invoking `load_local`.

---

## 2. Chrome Extension Issues

### Issue: Extension says "No Video" in Side Panel
- **Symptom**: The header displays "No Video" while YouTube is open.
- **Cause**:
  1. You are on the YouTube homepage, subscriptions, or search page rather than an individual video watch page.
  2. You loaded the extension unpacked after opening the tab, so the content script hasn't injected yet.
- **Fix**: Refresh the YouTube watch page (`F5`) or open a new video. The content script will detect the video ID immediately.

### Issue: "Could not connect to YouTube AI Assistant backend"
- **Symptom**: Side panel shows network connection error.
- **Cause**: The FastAPI server is not running on `http://127.0.0.1:8000`.
- **Fix**:
  1. Run `uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload` in PowerShell.
  2. Test `http://127.0.0.1:8000/health` in your browser.

### Issue: Side panel does not open when clicking the extension icon
- **Cause**: Chrome Side Panel API requires `openPanelOnActionClick: true` which is registered during extension installation.
- **Fix**: Go to `chrome://extensions`, click the Reload icon on **YouTube AI Assistant**, and click the extension icon again on a YouTube tab.

