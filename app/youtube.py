from fastapi import APIRouter, HTTPException
from app.schemas import YouTubeURL, YouTubeCommentsResponse, YouTubeTranscriptResponse
from app.services.youtube_service import extract_video_id, get_video_metadata, get_video_comments, get_video_transcript
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/youtube/metadata", response_model=dict)
async def get_youtube_metadata(payload: YouTubeURL):
    try:
        video_id = extract_video_id(payload.url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        metadata = get_video_metadata(video_id)
        if "error" in metadata:
            raise ValueError(metadata["error"])
        return metadata
    except Exception as e:
        logger.error(f"Metadata fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/youtube/comments", response_model=YouTubeCommentsResponse)
async def get_youtube_comments(payload: YouTubeURL):
    try:
        video_id = extract_video_id(payload.url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        comments = get_video_comments(video_id)
        return {"comments": comments}
    except Exception as e:
        logger.error(f"Comments fetch error: {e}")
        return {"comments": [], "error": str(e)}

@router.post("/youtube/transcript", response_model=YouTubeTranscriptResponse)
async def get_youtube_transcript(payload: YouTubeURL):
    try:
        video_id = extract_video_id(payload.url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        transcript = get_video_transcript(video_id)
        return {"transcript": transcript}
    except Exception as e:
        logger.error(f"Transcript fetch error: {e}")
        return {"transcript": "", "error": str(e)}