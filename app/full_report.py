from fastapi import APIRouter, HTTPException
from app.youtube import get_youtube_comments
from app.sentiment import analyze_comments
from app.services.nlp_service import categorize_comments, generate_content_report
from app.schemas import FullReportResponse, TextBatch, Analysis, Report
from app.config import get_log_config
import logging.config
import validators
import re

logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

full_report_router = APIRouter()

@full_report_router.post("/full-report", response_model=FullReportResponse)
async def generate_full_report(url: str):
    try:
        # Validate YouTube URL
        if not validators.url(url) or "youtube.com/watch?v=" not in url:
            logger.error(f"Invalid YouTube URL: {url}")
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # Extract video ID
        video_id_match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        if not video_id_match:
            logger.error(f"Could not extract video ID from URL: {url}")
            raise HTTPException(status_code=400, detail="Could not extract video ID")
        video_id = video_id_match.group(1)

        # Fetch comments
        comment_data = await get_youtube_comments(video_id)
        # Ensure comment_data is a TextBatch object
        if isinstance(comment_data, dict):
            logger.warning(f"Received dict instead of TextBatch for video ID: {video_id}")
            comment_data = TextBatch(**comment_data)

        if not comment_data.texts:
            logger.warning(f"No valid comments found for video ID: {video_id}")
            return FullReportResponse(
                metadata={
                    "video_id": video_id,
                    "url": url,
                    "comment_count": 0,
                    "likes": comment_data.likes,
                    "dislikes": comment_data.dislikes
                },
                analysis=Analysis(
                    comments=[],
                    report=Report(
                        summary="No comments available for analysis.",
                        sentiment_summary={"Positive": 0, "Neutral": 0, "Negative": 0},
                        categorized_comments={"most_interesting": [], "hot_takes": [], "questions": []},
                        actionable_insights=["Encourage viewer engagement to collect more comments."]
                    )
                ),
                exports={}
            )

        # Analyze comments
        analysis_results = await analyze_comments(comment_data)
        categorized_comments = categorize_comments(comment_data.texts)
        report = generate_content_report(
            transcription=comment_data.transcription,
            likes=comment_data.likes,
            dislikes=comment_data.dislikes,
            sentiment_results=analysis_results,
            categorized_comments=categorized_comments
        )

        return FullReportResponse(
            metadata={
                "video_id": video_id,
                "url": url,
                "comment_count": len(comment_data.texts),
                "likes": comment_data.likes,
                "dislikes": comment_data.dislikes
            },
            analysis=Analysis(
                comments=analysis_results,
                report=report
            ),
            exports={}  # Placeholder; integrate with export_service.py for PDF URLs
        )
    except Exception as e:
        logger.error(f"Error generating full report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating full report: {str(e)}")
    