from fastapi import APIRouter, HTTPException
from pydantic import HttpUrl
from app.youtube import get_youtube_comments
from app.sentiment import analyze_comments, generate_report
from app.schemas import TextBatch
import logging
import re

full_report_router = APIRouter()
logger = logging.getLogger(__name__)

@full_report_router.post("/full-report")
async def generate_full_report(url: HttpUrl):
    """
    Generate a full report by fetching YouTube comments and analyzing them.
    """
    try:
        # Extract video_id from URL
        video_id_match = re.search(r"(?:v=|youtu\.be/)([0-9A-Za-z_-]{11})", str(url))
        if not video_id_match:
            logger.error(f"Invalid YouTube URL: {url}")
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        video_id = video_id_match.group(1)
        logger.info(f"Processing video ID: {video_id}")

        # Fetch comments
        comment_data_dict = await get_youtube_comments(video_id)

        # Convert dictionary to TextBatch
        try:
            comment_data = TextBatch(**comment_data_dict)
        except Exception as e:
            logger.error(f"Error converting comment data to TextBatch: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing comment data: {str(e)}")

        # Analyze comments
        analysis_results = await analyze_comments(comment_data)

        # Generate report
        report = await generate_report(comment_data)

        # Post-process response
        # Round confidence to 2 decimal places
        for comment in analysis_results:
            comment["confidence"] = round(comment["confidence"], 2)

        # Limit hot_takes and questions to top 15
        report["categorized_comments"]["hot_takes"] = report["categorized_comments"]["hot_takes"][:15]
        report["categorized_comments"]["questions"] = report["categorized_comments"]["questions"][:15]

        # Combine results
        return {
            "metadata": {
                "video_id": video_id,
                "url": str(url),
                "comment_count": len(comment_data.texts),
                "likes": comment_data.likes,
                "dislikes": comment_data.dislikes
            },
            "analysis": {
                "comments": analysis_results,
                "report": report
            }
        }
    except Exception as e:
        logger.error(f"Error generating full report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating full report: {str(e)}")