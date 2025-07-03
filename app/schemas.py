from pydantic import BaseModel
from typing import List, Optional, Dict

class TextBatch(BaseModel):
    texts: List[str]
    transcription: Optional[str] = None
    likes: int = 0
    dislikes: int = 0

class CommentAnalysis(BaseModel):
    text: str
    sentiment: str
    confidence: float
    keywords: List[str]
    is_question: bool

class Report(BaseModel):
    summary: str
    sentiment_summary: Dict[str, float]
    categorized_comments: Dict[str, List[str]]
    actionable_insights: List[str]

class Metadata(BaseModel):
    video_id: str
    url: str
    comment_count: int
    likes: int
    dislikes: int

class Analysis(BaseModel):
    comments: List[CommentAnalysis]
    report: Report

class FullReportResponse(BaseModel):
    metadata: Metadata
    analysis: Analysis
    exports: Optional[Dict[str, str]] = None  # Optional to avoid breaking existing code