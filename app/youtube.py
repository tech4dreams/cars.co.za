from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.schemas import TextBatch
import os
from dotenv import load_dotenv
import logging

youtube_router = APIRouter()
logger = logging.getLogger(__name__)

load_dotenv("C:/Users/Seth.Valentine/cars.co.za/.env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

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
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)

        # Fetch video details for likes/dislikes and transcription
        video_request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        video_response = video_request.execute()
        video_data = video_response["items"][0]
        likes = int(video_data["statistics"].get("likeCount", 0))
        dislikes = int(video_data["statistics"].get("dislikeCount", 0))
        transcription = video_data["snippet"].get("description", "")

        return {
            "texts": comments,
            "transcription": transcription,
            "likes": likes,
            "dislikes": dislikes
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {str(e)}")