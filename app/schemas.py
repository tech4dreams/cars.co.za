# app/schemas.py
from pydantic import BaseModel
from typing import List

class TextBatch(BaseModel):
    texts: List[str]

    class Config:
        json_schema_extra = {  # Changed from schema_extra
            "example": {
                "texts": [
                    "This car is amazing!",
                    "Why is the audio quality so bad?",
                    "Average experience overall."
                ]
            }
        }

class SentimentResult(BaseModel):
    text: str
    sentiment: str
    confidence: float

    class Config:
        json_schema_extra = {  # Changed from schema_extra
            "example": {
                "text": "This car is amazing!",
                "sentiment": "positive",
                "confidence": 0.95
            }
        }

class KeywordResult(BaseModel):
    text: str
    keywords: List[str]

    class Config:
        json_schema_extra = {  # Changed from schema_extra
            "example": {
                "text": "This car is amazing!",
                "keywords": ["car", "review", "engine"]
            }
        }

class QuestionResult(BaseModel):
    text: str
    is_question: bool

    class Config:
        json_schema_extra = {  # Changed from schema_extra
            "example": {
                "text": "Why is the audio quality so bad?",
                "is_question": True
            }
        }