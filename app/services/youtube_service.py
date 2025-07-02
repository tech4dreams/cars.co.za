import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv("C:/Users/Seth.Valentine/cars.co.za/.env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|)", url)
    return video_id_match.group(1) if video_id_match else None

def get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata using YouTube API."""
    try:
        request = youtube.videos().list(part="snippet,statistics", id=video_id)
        response = request.execute()
        if not response["items"]:
            raise ValueError("Video not found")
        item = response["items"][0]
        return {
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "view_count": int(item["statistics"].get("viewCount", 0)),
            "like_count": int(item["statistics"].get("likeCount", 0)),
            "dislike_count": int(item["statistics"].get("dislikeCount", 0)),
            "comment_count": int(item["statistics"].get("commentCount", 0))
        }
    except HttpError as e:
        logger.error(f"Error fetching metadata: {e}")
        return {"error": str(e)}

def get_video_comments(video_id: str) -> list:
    """Fetch video comments using YouTube API."""
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )
        comments = []
        while request:
            response = request.execute()
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)
            request = youtube.commentThreads().list_next(request, response)
        return comments
    except HttpError as e:
        logger.error(f"Error fetching comments: {e}")
        return []

def get_video_transcript(video_id: str) -> str:
    """Fetch video transcript using youtube_transcript_api."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except TranscriptsDisabled:
        logger.warning("Transcripts disabled for this video")
        return ""
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        return ""

def fetch_youtube_data(url: str) -> dict:
    """Fetch all YouTube data (metadata, comments, transcript) from a URL."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    metadata = get_video_metadata(video_id)
    if "error" in metadata:
        raise ValueError(metadata["error"])

    comments = get_video_comments(video_id)
    transcript = get_video_transcript(video_id)

    return {
        "metadata": metadata,
        "comments": comments,
        "transcript": transcript
    }