from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.schemas import TextBatch
from app.config import settings, API_ENDPOINTS, get_log_config
import logging.config

youtube_router = APIRouter()
logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

@youtube_router.get("/youtube/comments", response_model=TextBatch)
async def get_youtube_comments(video_id: str):
    """
    Fetch YouTube comments for a given video ID.
    """
    try:
        logger.info(f"Fetching comments for video ID: {video_id}")
        comments = []
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=settings.max_comments_per_video,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            if isinstance(comment, str) and comment.strip():
                comments.append(comment)
            else:
                logger.warning(f"Skipping invalid comment for video ID: {video_id}")

        video_request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        video_response = video_request.execute()
        if not video_response.get("items"):
            logger.error(f"No video data found for video ID: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")

        video_data = video_response["items"][0]
        likes = int(video_data["statistics"].get("likeCount", 0))
        dislikes = int(video_data["statistics"].get("dislikeCount", 0))
        transcription = video_data["snippet"].get("description", "")

        return TextBatch(
            texts=comments,
            transcription=transcription,
            likes=likes,
            dislikes=dislikes
        )
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {str(e)}")
    