from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class YouTubeURL(BaseModel):
    url: str

class TextBatch(BaseModel):
    texts: List[str]
    transcription: str = ""
    likes: int = 0
    dislikes: int = 0

class SentimentResult(BaseModel):
    text: str
    sentiment: str
    confidence: float

class KeywordResult(BaseModel):
    text: str
    keywords: List[str]

class QuestionResult(BaseModel):
    text: str
    is_question: bool

class CategorizedComments(BaseModel):
    most_interesting: List[str]
    hot_takes: List[str]
    questions: List[str]

class ReportSummary(BaseModel):
    summary: str
    sentiment_summary: Dict[str, float]
    categorized_comments: CategorizedComments
    actionable_insights: List[str]

class SentimentResponse(BaseModel):
    sentiment: List[SentimentResult]
    keywords: List[KeywordResult]
    questions: List[QuestionResult]

class ReportResponse(BaseModel):
    summary: str
    sentiment_summary: Dict[str, float]
    categorized_comments: CategorizedComments
    actionable_insights: List[str]

class YouTubeCommentsResponse(BaseModel):
    comments: List[str]
    error: Optional[str] = None

class YouTubeTranscriptResponse(BaseModel):
    transcript: str
    error: Optional[str] = None

class FullReportResponse(BaseModel):
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    report: ReportResponse
    exports: Dict[str, str]