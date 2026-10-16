from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.core.exceptions import AppException
from backend.app.core.logging import logger
from backend.app.services.transcript_service import TranscriptResult
from backend.app.utils.video_id import build_youtube_watch_url


class DocumentService:
    """Service responsible for transforming transcript snippets into chunked LangChain Documents with timestamps."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        )

    def create_documents(self, transcript: TranscriptResult) -> List[Document]:
        """
        Group snippets into timestamped sections and split them into indexed chunks.
        Every chunk preserves start_seconds, end_seconds, and a direct timestamped video URL.
        """
        if not transcript.snippets:
            raise AppException("Cannot create documents from an empty transcript.", status_code=400)

        # 1. Group consecutive snippets into coherent time blocks (~30-45 seconds or ~600 chars)
        raw_sections: List[Document] = []
        current_texts: List[str] = []
        block_start = transcript.snippets[0].start
        block_end = block_start

        for snippet in transcript.snippets:
            snippet_end = snippet.start + snippet.duration
            current_texts.append(snippet.text)
            block_end = max(block_end, snippet_end)

            combined_len = sum(len(t) for t in current_texts)
            # When block reaches ~500 chars or 40 seconds, create a section document
            if combined_len >= 500 or (block_end - block_start) >= 40.0:
                section_text = " ".join(current_texts)
                raw_sections.append(
                    Document(
                        page_content=section_text,
                        metadata={
                            "video_id": transcript.video_id,
                            "start_seconds": round(block_start, 2),
                            "end_seconds": round(block_end, 2),
                            "language": transcript.language,
                            "is_generated": transcript.is_generated,
                            "source": build_youtube_watch_url(transcript.video_id, int(block_start)),
                        },
                    )
                )
                current_texts = []
                block_start = snippet_end

        # Flush remaining snippets
        if current_texts:
            section_text = " ".join(current_texts)
            raw_sections.append(
                Document(
                    page_content=section_text,
                    metadata={
                        "video_id": transcript.video_id,
                        "start_seconds": round(block_start, 2),
                        "end_seconds": round(block_end, 2),
                        "language": transcript.language,
                        "is_generated": transcript.is_generated,
                        "source": build_youtube_watch_url(transcript.video_id, int(block_start)),
                    },
                )
            )

        # 2. Split into final chunks while retaining metadata
        chunked_docs = self.splitter.split_documents(raw_sections)

        if not chunked_docs:
            raise AppException("Failed to generate document chunks from transcript.", status_code=500)

        # Assign unique chunk indices
        for idx, doc in enumerate(chunked_docs):
            doc.metadata["chunk_index"] = idx

        logger.info(
            f"Created {len(chunked_docs)} chunks from {len(transcript.snippets)} snippets "
            f"for video {transcript.video_id}"
        )

        return chunked_docs

