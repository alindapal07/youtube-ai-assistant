from fastapi import APIRouter, Depends, Path
from backend.app.api.dependencies import get_vector_store_service
from backend.app.schemas.video import (
    VideoInfoResponse,
    VideoProcessRequest,
    VideoProcessResponse,
)
from backend.app.services.vector_store_service import VectorStoreService
from backend.app.utils.video_id import extract_video_id

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("/process", response_model=VideoProcessResponse)
async def process_video(
    payload: VideoProcessRequest,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Fetch transcript, generate embeddings, and build or reuse FAISS index for a YouTube video.
    """
    _, metadata, was_cached = await vector_store_service.get_or_create_index(
        video_id=payload.video_id,
        language=payload.language,
    )

    return VideoProcessResponse(
        success=True,
        video_id=metadata.video_id,
        title=metadata.title,
        status="ready",
        chunks_created=metadata.total_chunks,
        cached=was_cached,
    )


@router.get("/{video_id}", response_model=VideoInfoResponse)
async def get_video_info(
    video_id: str = Path(..., description="11-character YouTube video ID"),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Retrieve processing status and safe metadata for a YouTube video without exposing raw transcript or filesystem paths.
    """
    canonical_id = extract_video_id(video_id)
    metadata = vector_store_service.get_metadata(canonical_id)

    if metadata is not None:
        title = metadata.title
        if not title:
            from backend.app.services.transcript_service import TranscriptService
            title = TranscriptService.fetch_video_title(canonical_id)
        return VideoInfoResponse(
            video_id=canonical_id,
            title=title,
            status="ready",
            indexed=True,
            chunks_count=metadata.total_chunks,
            metadata=metadata,
        )

    from backend.app.services.transcript_service import TranscriptService
    video_title = TranscriptService.fetch_video_title(canonical_id)

    return VideoInfoResponse(
        video_id=canonical_id,
        title=video_title,
        status="not_indexed",
        indexed=False,
        chunks_count=None,
        metadata=None,
    )

