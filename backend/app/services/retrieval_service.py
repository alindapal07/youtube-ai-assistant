from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from backend.app.core.config import get_settings
from backend.app.core.logging import logger


class RetrievalService:
    """Configures and runs MMR retrieval on FAISS vector stores."""

    def __init__(
        self,
        search_type: str = "mmr",
        k: Optional[int] = None,
        fetch_k: Optional[int] = None,
        lambda_mult: Optional[float] = None,
    ):
        settings = get_settings()
        self.search_type = search_type
        self.k = k if k is not None else settings.RETRIEVAL_K
        self.fetch_k = fetch_k if fetch_k is not None else settings.RETRIEVAL_FETCH_K
        self.lambda_mult = lambda_mult if lambda_mult is not None else settings.RETRIEVAL_LAMBDA_MULT

    def retrieve(self, vector_store: FAISS, query: str) -> List[Document]:
        """
        Execute MMR search to retrieve relevant, diverse transcript chunks.
        """
        logger.info(f"Executing MMR retrieval (k={self.k}, fetch_k={self.fetch_k}) for query: '{query[:60]}...'")

        retriever = vector_store.as_retriever(
            search_type=self.search_type,
            search_kwargs={
                "k": self.k,
                "fetch_k": self.fetch_k,
                "lambda_mult": self.lambda_mult,
            },
        )

        documents = retriever.invoke(query)
        logger.info(f"Retriever returned {len(documents)} relevant chunks.")
        return documents

