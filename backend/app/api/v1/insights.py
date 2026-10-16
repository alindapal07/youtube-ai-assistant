from fastapi import APIRouter, Depends, Path
from backend.app.api.dependencies import get_insights_service
from backend.app.schemas.chat import (
    InterviewQuestionsResponse,
    StudyNotesResponse,
    VideoSummaryResponse,
)
from backend.app.services.insights_service import InsightsService
from backend.app.utils.video_id import extract_video_id

router = APIRouter(prefix="/videos", tags=["Insights"])


@router.post("/{video_id}/summary", response_model=VideoSummaryResponse)
async def get_video_summary(
    video_id: str = Path(..., description="Target YouTube video ID"),
    insights_service: InsightsService = Depends(get_insights_service),
):
    """Generate a transcript-grounded executive summary."""
    canonical_id = extract_video_id(video_id)
    return await insights_service.generate_summary(canonical_id)


@router.post("/{video_id}/notes", response_model=StudyNotesResponse)
async def get_study_notes(
    video_id: str = Path(..., description="Target YouTube video ID"),
    insights_service: InsightsService = Depends(get_insights_service),
):
    """Generate structured study notes and key takeaways."""
    canonical_id = extract_video_id(video_id)
    return await insights_service.generate_study_notes(canonical_id)


@router.post("/{video_id}/questions", response_model=InterviewQuestionsResponse)
async def get_interview_questions(
    video_id: str = Path(..., description="Target YouTube video ID"),
    insights_service: InsightsService = Depends(get_insights_service),
):
    """Generate challenging interview / revision questions based on the video transcript."""
    canonical_id = extract_video_id(video_id)
    return await insights_service.generate_questions(canonical_id)

