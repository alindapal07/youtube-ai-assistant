from fastapi import APIRouter, Depends, Query
from backend.app.api.dependencies import get_chat_service
from backend.app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from backend.app.schemas.common import BaseResponse
from backend.app.services.chat_service import ChatService
from backend.app.utils.video_id import extract_video_id

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Submit a question regarding the processed video and receive an answer grounded in the transcript.
    """
    return await chat_service.answer_question(
        video_id=payload.video_id,
        session_id=payload.session_id,
        question=payload.question,
    )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    video_id: str = Query(..., description="Target YouTube video ID"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Retrieve conversation history for a specific video session.
    """
    canonical_id = extract_video_id(video_id)
    messages = chat_service.get_history(video_id=canonical_id, session_id=session_id)
    return ChatHistoryResponse(
        success=True,
        video_id=canonical_id,
        session_id=session_id,
        messages=messages,
    )


@router.delete("/history/{session_id}", response_model=BaseResponse)
async def clear_chat_history(
    session_id: str,
    video_id: str = Query(..., description="Target YouTube video ID"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Clear conversation history for a specific video session.
    """
    canonical_id = extract_video_id(video_id)
    chat_service.clear_history(video_id=canonical_id, session_id=session_id)
    return BaseResponse(
        success=True,
        message=f"Conversation history cleared for video {canonical_id} and session {session_id}.",
    )

