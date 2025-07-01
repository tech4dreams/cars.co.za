from fastapi import APIRouter, HTTPException
from app.services.youtube_service import get_video_comments
from app.schemas import YouTubeURL, YouTubeCommentsResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/comments", response_model=YouTubeCommentsResponse)
async def fetch_comments(payload: YouTubeURL):
    video_id = payload.extract_video_id()
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        comments = await get_video_comments(video_id, max_results=300)
        logger.info(f"Fetched {len(comments)} comments for video {video_id}")
    except Exception as e:
        logger.warning(f"Failed to fetch comments for {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch YouTube comments")

    if not comments:
        logger.info(f"No comments found for video {video_id} or comments are disabled.")
        return {"video_id": video_id, "comments": []}

    return {"video_id": video_id, "comments": comments}
