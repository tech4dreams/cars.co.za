# app/sentiment.py
from fastapi import APIRouter
from app.schemas import TextBatch
from app.services.nlp_service import analyze_sentiment, extract_keywords, find_questions

sentiment_router = APIRouter()

@sentiment_router.post("/sentiment")
async def sentiment_analysis(data: TextBatch):
    """
    Analyze sentiment, extract keywords, and detect questions for a batch of texts.
    """
    sentiment_results = analyze_sentiment(data.texts)
    keywords = extract_keywords(data.texts)
    questions = find_questions(data.texts)
    return {
        "sentiment": sentiment_results,
        "keywords": keywords,
        "questions": questions
    }