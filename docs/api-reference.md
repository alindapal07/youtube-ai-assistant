# YouTube AI Assistant — API Reference

Base URL: `http://127.0.0.1:8000/api/v1`

---

## 1. Health Endpoints

### `GET /health`
Returns the application liveness status.

**Response (200 OK):**
```json
{
  "status": "ok",
  "environment": "development",
  "version": "1.0.0"
}
```

### `GET /api/v1/health/ready`
Readiness probe verifying Groq API key configuration, storage write access, and embedding service status.

**Response (200 OK):**
```json
{
  "status": "ready",
  "groq_configured": true,
  "embedding_model_ready": true,
  "storage_writable": true
}
```

---

## 2. Video Processing

### `POST /api/v1/videos/process`
Ingests the official transcript for a YouTube video, splits into timestamped chunks, generates dense vector embeddings using `all-MiniLM-L6-v2`, and builds/caches a local FAISS index.

**Request:**
```json
{
  "video_id": "Gfr50f6ZBvo",
  "language": "en"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "video_id": "Gfr50f6ZBvo",
  "status": "ready",
  "chunks_created": 34,
  "cached": false
}
```

### `GET /api/v1/videos/{video_id}`
Checks whether a video has already been indexed and returns safe metadata without exposing filesystem paths.

**Response (200 OK — Indexed):**
```json
{
  "video_id": "Gfr50f6ZBvo",
  "status": "ready",
  "indexed": true,
  "chunks_count": 34,
  "metadata": {
    "video_id": "Gfr50f6ZBvo",
    "video_url": "https://www.youtube.com/watch?v=Gfr50f6ZBvo",
    "language": "en",
    "is_generated": false,
    "total_chunks": 34,
    "created_at": "2026-10-14T13:00:00Z",
    "expires_at": "2026-10-15T13:00:00Z"
  }
}
```

---

## 3. Grounded Chat & Q&A

### `POST /api/v1/chat`
Answers a user question regarding an indexed video. Uses MMR retrieval to extract the 4 most relevant and diverse chunks from FAISS, formatting an anti-jailbreak prompt for Groq LLM.

**Request:**
```json
{
  "video_id": "Gfr50f6ZBvo",
  "session_id": "user-session-123",
  "question": "What is the primary concept discussed in this video?"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "video_id": "Gfr50f6ZBvo",
  "answer": "The video discusses Retrieval-Augmented Generation (RAG) using LangChain and vector stores to ground LLMs.",
  "sources": [
    {
      "text": "In this video we are building a RAG pipeline with vector databases...",
      "start_seconds": 12.0,
      "end_seconds": 38.5,
      "video_url": "https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=12s"
    }
  ]
}
```

### `GET /api/v1/chat/history/{session_id}?video_id={video_id}`
Retrieves session-isolated message history.

**Response (200 OK):**
```json
{
  "success": true,
  "video_id": "Gfr50f6ZBvo",
  "session_id": "user-session-123",
  "messages": [
    {
      "role": "user",
      "content": "What is LangChain?",
      "sources": [],
      "timestamp": "2026-10-14T13:05:00Z"
    },
    {
      "role": "assistant",
      "content": "LangChain is a framework for developing applications powered by language models.",
      "sources": [],
      "timestamp": "2026-10-14T13:05:03Z"
    }
  ]
}
```

### `DELETE /api/v1/chat/history/{session_id}?video_id={video_id}`
Clears session conversation history.

---

## 4. Video Insights

### `POST /api/v1/videos/{video_id}/summary`
Generates an executive overview, major milestones, and key conclusions from the transcript.

### `POST /api/v1/videos/{video_id}/notes`
Generates structured study notes and an actionable list of key takeaways.

### `POST /api/v1/videos/{video_id}/questions`
Generates 5-8 technical interview / revision questions with grounded answer guidelines.

