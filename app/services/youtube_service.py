import time
import logging
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

from googleapiclient.discovery import build
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

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
