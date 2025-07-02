# Request/response models

from pydantic import BaseModel
import re
from typing import List, Optional

class YouTubeURL(BaseModel):
    url: str

    def extract_video_id(self) -> str:
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", self.url)
        return match.group(1) if match else None

class YouTubeCommentsResponse(BaseModel):
    video_id: str
    comments: List[str]

class YouTubeTranscriptResponse(BaseModel):
    video_id: str
    transcript: Optional[str]
    message: Optional[str] = None

class YouTubeMetadataResponse(BaseModel):
    videoId: str
    title: str
    description: Optional[str]
    publishedAt: str
    channelTitle: str
    viewCount: int
    likeCount: int
    commentCount: int