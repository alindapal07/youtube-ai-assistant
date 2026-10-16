# YouTube AI Assistant — Real-Time Browser Extension

A production-minded, modular Chrome Extension and AI backend that allows users to interact with any supported YouTube video's transcript through a real-time side-panel chatbot.

Built with **Chrome Extension Manifest V3**, **React 18**, **TypeScript**, **Vite**, **Python FastAPI**, **LangChain**, **Hugging Face sentence-transformers**, **FAISS CPU**, and **Groq LLM**.

---

## 1. Features

- **Chrome Side Panel Integration**: Seamless side panel opens alongside YouTube videos without interrupting viewing.
- **Real-Time Video Detection**: Automatically extracts video ID on load and tracks client-side single-page app (SPA) navigation on YouTube (`yt-navigate-finish`, `popstate`).
- **Grounded AI Question Answering**: Questions are answered strictly using retrieved transcript context via Groq Cloud (`openai/gpt-oss-20b`).
- **Verified Timestamp Citations**: Every answer includes clickable timestamp chips (`⏱ 02:15 - 02:45`) linking directly to that exact moment in the video.
- **Video Insights Toolbar**:
  - ⚡ **Summarize**: Generates an executive overview, major themes, and conclusion.
  - 📝 **Study Notes**: Generates comprehensive structured notes and key takeaways.
  - 🎯 **Interview Qs**: Generates technical revision questions with grounded answer keys.
- **Session & Video Isolation**: Switching YouTube videos automatically isolates conversations and checks for cached vector stores, ensuring zero context leakage between videos.
- **Local FAISS Index Persistence**: Saves and loads chunk embeddings locally with metadata integrity validation and TTL expiration.
- **Anti-Jailbreak Protection**: Strict system prompt safeguards treating YouTube transcripts as untrusted user data.

---

## 2. Technology Stack

### Frontend & Extension
- **Chrome Extension Manifest V3** (Side Panel API, Runtime Messaging, Storage API)
- **React 18** with **TypeScript**
- **Vite 5** for lightning-fast bundling
- Modern dark/light CSS design tokens with responsive layout

### Backend & AI
- **Python 3.12**
- **FastAPI** + **Uvicorn**
- **Pydantic v2** & **Pydantic Settings** for type-safe validation
- **LangChain** (`langchain-core`, `langchain-text-splitters`, `langchain-community`)
- **youtube-transcript-api** for transcript retrieval
- **Hugging Face Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **FAISS CPU** for vector similarity search
- **Groq LLM**: `openai/gpt-oss-20b` (low-latency inference)

---

## 3. Project Structure

```
YoutubeTranscriptPlugin/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application factory and lifespan
│   │   ├── api/
│   │   │   ├── dependencies.py      # Dependency injection providers
│   │   │   └── v1/
│   │   │       ├── router.py        # Centralized v1 routing
│   │   │       ├── health.py        # Health and readiness probes
│   │   │       ├── videos.py        # Process and inspect video endpoints
│   │   │       ├── chat.py          # Grounded chat and history endpoints
│   │   │       └── insights.py      # Summary, notes, and question endpoints
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings configuration
│   │   │   ├── logging.py           # Structured logger with secret redaction
│   │   │   └── exceptions.py        # Centralized HTTP application exceptions
│   │   ├── schemas/
│   │   │   ├── common.py            # BaseResponse, ErrorResponse, Health schemas
│   │   │   ├── video.py             # VideoProcessRequest and VideoInfo schemas
│   │   │   └── chat.py              # ChatRequest, ChatResponse, SourceReference
│   │   ├── services/
│   │   │   ├── transcript_service.py # youtube-transcript-api integration
│   │   │   ├── document_service.py   # Chunking preserving start/end seconds
│   │   │   ├── embedding_service.py  # Thread-safe HuggingFace MiniLM singleton
│   │   │   ├── vector_store_service.py # Indexing and deduplication coordinator
│   │   │   ├── retrieval_service.py  # MMR search configuration
│   │   │   ├── rag_service.py        # Prompt assembly & Groq invocation
│   │   │   ├── chat_service.py       # Session-isolated memory
│   │   │   └── insights_service.py   # Summary, study notes, interview Qs
│   │   ├── repositories/
│   │   │   └── vector_store_repository.py # Disk persistence & metadata checks
│   │   ├── prompts/
│   │   │   ├── chat_prompt.py       # Anti-jailbreak grounded chat prompt
│   │   │   └── insights_prompt.py   # Summary, notes, and Qs prompts
│   │   ├── utils/
│   │   │   ├── video_id.py          # Multi-format YouTube ID extraction
│   │   │   └── text_processing.py   # Cleaning and timestamp formatters
│   │   └── storage/
│   │       └── .gitkeep             # Local FAISS index persistence root
│   ├── tests/
│   │   ├── test_health.py           # Health and readiness tests
│   │   ├── test_video_id.py         # ID validation tests across 6 URL formats
│   │   ├── test_transcript_service.py # Caption fallback & chunking tests
│   │   ├── test_chat.py             # Session isolation & endpoint tests
│   │   └── test_rag_service.py      # MMR retrieval & citation tests
│   ├── .env.example
│   ├── .gitignore
│   ├── pyproject.toml
│   └── README.md
│
├── extension/
│   ├── public/
│   │   └── icons/                   # 16px, 48px, 128px extension icons
│   ├── src/
│   │   ├── background/
│   │   │   └── service-worker.ts    # Sidepanel behavior & message routing
│   │   ├── content/
│   │   │   └── youtube-content.ts   # Real-time SPA navigation observer
│   │   ├── sidepanel/
│   │   │   ├── index.html           # HTML container
│   │   │   ├── main.tsx             # React DOM root
│   │   │   ├── App.tsx              # Application layout & state wiring
│   │   │   ├── components/          # Reusable UI components
│   │   │   ├── hooks/               # useCurrentVideo, useVideoProcessing, useChat
│   │   │   ├── services/            # Typed fetch API client
│   │   │   ├── types/               # TypeScript interfaces
│   │   │   └── styles/              # Global and component stylesheets
│   │   ├── shared/
│   │   │   ├── messages.ts          # Typed message definitions
│   │   │   └── constants.ts         # Base URL and limits
│   │   └── manifest.json            # Chrome Manifest V3 specification
│   ├── scripts/
│   │   └── build-extension.mjs      # Build & packaging script
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── .gitignore
│   └── README.md
│
├── docs/
│   ├── architecture.md              # Diagrams and detailed data flows
│   ├── api-reference.md             # Request and response specs
│   └── troubleshooting.md           # Solutions for common issues
│
├── YoutubeVideoChatAI.py            # Original reference script (preserved)
├── .gitignore
└── README.md
```

---

## 4. Getting Started (Windows PowerShell)

### Prerequisites
- **Python 3.11+** installed (verified with Python 3.12)
- **Node.js 18+** installed (verified with Node v22.17.0, npm 11.7.0)
- **uv** installed (or standard pip)
- A free **Groq Cloud API Key** from [console.groq.com](https://console.groq.com/keys)

---

### Step 1: Backend Setup & Configuration

1. Open PowerShell in the workspace root directory:
```powershell
cd "c:\Users\alind\OneDrive\Desktop\VS CODE\Langchain\YoutubeTranscriptPlugin"
```

2. Create your `.env` configuration from the example:
```powershell
Copy-Item backend\.env.example .env
```

3. Open `.env` in your text editor and add your Groq API key:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
API_HOST=127.0.0.1
API_PORT=8000
```

4. Run the automated backend test suite:
```powershell
uv run pytest
```
*All 21 unit tests run offline using mocks without consuming API credits.*

5. Start the FastAPI server:
```powershell
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*The server will start at `http://127.0.0.1:8000`. You can inspect the interactive Swagger docs at `http://127.0.0.1:8000/docs`.*

---

### Step 2: Build the Chrome Extension

Open a second PowerShell window:

1. Navigate to the `extension` folder:
```powershell
cd "c:\Users\alind\OneDrive\Desktop\VS CODE\Langchain\YoutubeTranscriptPlugin\extension"
```

2. Install frontend dependencies:
```powershell
npm install
```

3. Run TypeScript type check and compile the extension:
```powershell
npm run lint
npm run build
```
*The built, unpacked extension is generated in `extension/dist`.*

---

### Step 3: Load Extension into Google Chrome

1. Open Google Chrome.
2. In the URL bar, go to `chrome://extensions`.
3. In the top-right corner, toggle on **Developer mode**.
4. Click the **Load unpacked** button.
5. In the file picker, select:
   `c:\Users\alind\OneDrive\Desktop\VS CODE\Langchain\YoutubeTranscriptPlugin\extension\dist`
6. You will see **YouTube AI Assistant** (version 1.0.0) appear in your extensions list.

---

### Step 4: Test Real-Time Video Interaction

1. Open any YouTube video with captions (e.g. `https://www.youtube.com/watch?v=Gfr50f6ZBvo`).
2. Click the **YouTube AI Assistant** icon in the Chrome toolbar.
3. The Chrome Side Panel opens. It immediately detects the video and displays its title.
4. Click **Process Video**. The backend retrieves the transcript and indexes it in FAISS.
5. Ask any question in the input box, or click **⚡ Summarize**, **📝 Study Notes**, or **🎯 Interview Qs**.
6. Notice the verified timestamp citation chips (e.g. `⏱ 01:20 - 01:50`). Clicking a chip jumps directly to that timestamp in YouTube.
7. Click another video on YouTube. The side panel automatically transitions to the new video ID, resets conversation state, and allows you to process the new video.

---

## 5. Security Architecture

1. **No Frontend Secrets**: The Groq API key is strictly maintained on the backend in `.env` and never transferred to the browser or extension storage.
2. **Untrusted Data Sanitization**: Transcript contents are explicitly treated as untrusted data in LLM prompts. Prompt injection attempts embedded within captions are ignored by the assistant.
3. **Safe FAISS Deserialization**: `FAISS.load_local` is only called after parsing and validating `metadata.json`, verifying embedding model version compatibility, and checking TTL expiration.
4. **Log Masking**: Custom logging filter automatically masks `GROQ_API_KEY` from terminal and file logs.

---

## 6. Current Limitations & Production Deployment

- **Captions Required**: The extension requires closed captions (manual or auto-generated) on the target YouTube video. Videos with caption tracks disabled cannot be ingested.
- **Local Storage**: FAISS indexes are currently stored on the local filesystem. For a distributed cloud deployment, migrate `VectorStoreRepository` to a managed vector database (e.g. Pinecone, Milvus, Qdrant, or MongoDB Atlas Vector Search).
- **Multi-user Authentication**: The local development server allows all localhost requests via CORS. In production, configure JWT bearer authentication or API keys on the `/api/v1` routes.

