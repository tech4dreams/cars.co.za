from fastapi import APIRouter, HTTPException
from app.services.youtube_service import get_video_comments, get_video_transcript
from app.schemas import YouTubeURL, YouTubeCommentsResponse
from fastapi.responses import JSONResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/comments", response_model=YouTubeCommentsResponse)
async def fetch_comments(payload: YouTubeURL):
    video_id = payload.extract_video_id()
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        comments = get_video_comments(video_id, max_results=300)
        logger.info(f"Fetched {len(comments)} comments for video {video_id}")
    except Exception as e:
        logger.warning(f"Failed to fetch comments for {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch YouTube comments")

    if not comments:
        logger.info(f"No comments found for video {video_id} or comments are disabled.")
        return {"video_id": video_id, "comments": []}

    return {"video_id": video_id, "comments": comments}

@router.post("/transcript")
def fetch_transcript(payload: YouTubeURL):
    video_id = payload.extract_video_id()
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    transcript = get_video_transcript(video_id)
    if not transcript:
        return JSONResponse(content={"video_id": video_id, "transcript": None, "message": "No transcript available."}, status_code=200)

    return {"video_id": video_id, "transcript": transcript}
