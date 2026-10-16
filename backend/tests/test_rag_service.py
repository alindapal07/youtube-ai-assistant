from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from backend.app.schemas.chat import SourceReference
from backend.app.services.rag_service import RAGService
from backend.app.services.retrieval_service import RetrievalService


def test_build_sources():
    rag_service = RAGService(retrieval_service=MagicMock())
    docs = [
        Document(
            page_content="RAG allows models to ground responses.",
            metadata={
                "start_seconds": 12.0,
                "end_seconds": 25.0,
                "source": "https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=12s",
            },
        ),
        Document(
            page_content="FAISS provides fast similarity search.",
            metadata={
                "start_seconds": 30.0,
                "end_seconds": 45.0,
                "source": "https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=30s",
            },
        ),
    ]

    sources = rag_service.build_sources(docs, "Gfr50f6ZBvo")
    assert len(sources) == 2
    assert isinstance(sources[0], SourceReference)
    assert sources[0].start_seconds == 12.0
    assert sources[0].end_seconds == 25.0
    assert "https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=12s" in sources[0].video_url


def test_answer_query_with_mocked_llm():
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = [
        Document(
            page_content="LangChain is a framework for developing LLM applications.",
            metadata={"start_seconds": 15.0, "end_seconds": 25.0},
        )
    ]

    mock_chain_result = "LangChain is a framework for LLM applications based on the transcript."
    mock_llm = RunnableLambda(lambda x: AIMessage(content=mock_chain_result))

    rag_service = RAGService(retrieval_service=mock_retrieval, llm=mock_llm)

    mock_vector_store = MagicMock()
    answer, sources = rag_service.answer_query(
        vector_store=mock_vector_store,
        video_id="Gfr50f6ZBvo",
        question="What is LangChain?",
    )

    assert answer == mock_chain_result
    assert len(sources) == 1
    assert sources[0].start_seconds == 15.0
