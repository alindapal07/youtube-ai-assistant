# YouTube AI Assistant - Backend API

Production-minded, asynchronous FastAPI backend powering the YouTube AI Assistant Chrome Extension. Integrates LangChain, Hugging Face embeddings (`sentence-transformers/all-MiniLM-L6-v2`), FAISS CPU vector index persistence, and Groq LLM (`openai/gpt-oss-20b`).

---

## Features

- **YouTube Transcript Ingestion**: Retrieves official manual and auto-generated transcripts with precise timing metadata via `youtube-transcript-api`.
- **Timestamped Document Chunking**: Groups and splits transcript text while preserving segment start and end seconds for exact citation links.
- **Persistent Vector Storage**: Creates and manages disk-persisted FAISS vector stores with metadata tracking and expiration (TTL).
- **MMR Diversity Retrieval**: Uses Maximal Marginal Relevance (MMR) retrieval (`k=4`, `fetch_k=20`, `lambda_mult=0.5`) to retrieve balanced, diverse context chunks.
- **RAG Generation via Groq**: Fast LLM inference with anti-jailbreak prompt protection and strictly grounded answers.
- **Session & Video Isolated Conversations**: Chat history is strictly separated by `video_id` and `session_id`.
- **Grounded Video Insights**: Endpoints to generate executive summaries, structured study notes with key takeaways, and technical interview questions.
- **Centralized Exception Handling & Security**: Pydantic request/response validation, API key masking in logs, and no filesystem path exposure.

---

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── health.py
│   │       ├── videos.py
│   │       ├── chat.py
│   │       └── insights.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── video.py
│   │   └── chat.py
│   ├── services/
│   │   ├── transcript_service.py
│   │   ├── document_service.py
│   │   ├── embedding_service.py
│   │   ├── vector_store_service.py
│   │   ├── retrieval_service.py
│   │   ├── rag_service.py
│   │   ├── chat_service.py
│   │   └── insights_service.py
│   ├── repositories/
│   │   └── vector_store_repository.py
│   ├── prompts/
│   │   ├── chat_prompt.py
│   │   └── insights_prompt.py
│   ├── utils/
│   │   ├── video_id.py
│   │   └── text_processing.py
│   ├── storage/
│   │   └── .gitkeep
│   └── main.py
├── tests/
│   ├── test_health.py
│   ├── test_video_id.py
│   ├── test_transcript_service.py
│   ├── test_chat.py
│   └── test_rag_service.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Setup & Running

### 1. Environment Configuration

Copy `.env.example` to `.env` and fill in your Groq API key:

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env`:
```ini
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=openai/gpt-oss-20b
API_HOST=127.0.0.1
API_PORT=8000
```

### 2. Start the Backend Server

Using `uv`:

```powershell
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The server will be available at:
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### 3. Run Tests

```powershell
uv run pytest
```

