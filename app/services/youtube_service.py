import time
import logging
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

from googleapiclient.discovery import build
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_video_metadata(video_id: str) -> dict:
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        items = response.get("items", [])
        if not items:
            return {}

        video = items[0]
        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})

        return {
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "publishedAt": snippet.get("publishedAt"),
            "channelTitle": snippet.get("channelTitle"),
            "viewCount": int(stats.get("viewCount", 0)),
            "likeCount": int(stats.get("likeCount", 0)),
            "commentCount": int(stats.get("commentCount", 0)),
            "videoId": video_id
        }

    except Exception as e:
        logger.warning(f"Error fetching video metadata for {video_id}: {e}")
        return {}

def get_video_comments(video_id: str, max_results: int = 100) -> list[str]:
    comments = []
    retries = 3
    delay = 2  # seconds

    try:
        req = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )

        while req and len(comments) < max_results:
            for attempt in range(retries):
                try:
                    res = req.execute()
                    break  # success!
                except HttpError as e:
                    if e.resp.status in [403, 429, 500, 503]:
                        logger.warning(f"API quota or temporary error (status {e.resp.status}). Retrying...")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"Fatal error while fetching comments: {e}")
                        raise
            else:
                # If we exhausted all retries
                raise Exception("YouTube API failed after multiple retries.")

            for item in res.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(text)
                if len(comments) >= max_results:
                    break

            req = youtube.commentThreads().list_next(req, res)

    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        raise

    logger.info(f"Fetched {len(comments)} comments for video {video_id}")
    return comments

def get_video_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        full_text = " ".join([entry["text"] for entry in transcript])
        return full_text
    except TranscriptsDisabled:
        logger.info(f"Transcripts are disabled for video {video_id}")
        return ""
    except NoTranscriptFound:
        logger.info(f"No transcript found for video {video_id}")
        return ""
    except Exception as e:
        logger.warning(f"Error fetching transcript for video {video_id}: {e}")
        return ""
