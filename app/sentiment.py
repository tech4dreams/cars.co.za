from fastapi import APIRouter, HTTPException
from app.schemas import TextBatch
from app.services.nlp_service import analyze_sentiment, extract_keywords, find_questions, generate_content_report, categorize_comments
from app.services.export_service import export_to_json, export_to_csv
import logging

sentiment_router = APIRouter()
logger = logging.getLogger(__name__)

@sentiment_router.post("/sentiment")
async def analyze_comments(batch: TextBatch):
    """
    Analyze sentiment, extract keywords, and identify questions from a batch of texts.
    """
    try:
        sentiment_results = analyze_sentiment(batch.texts)
        keyword_results = extract_keywords(batch.texts)
        question_results = find_questions(batch.texts)

        # Combine results per comment
        combined_results = []
        for s, k, q in zip(sentiment_results, keyword_results, question_results):
            if s["text"] == k["text"] == q["text"]:
                combined_results.append({
                    "text": s["text"],
                    "sentiment": s["sentiment"],
                    "confidence": s["confidence"],
                    "keywords": k["keywords"],
                    "is_question": q["is_question"]
                })
            else:
                logger.error("Mismatch in text alignment for sentiment, keywords, or questions")
                raise HTTPException(status_code=500, detail="Internal server error: text alignment mismatch")

        return combined_results
    except Exception as e:
        logger.error(f"Error in analyze_comments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing comments: {str(e)}")

@sentiment_router.post("/report")
async def generate_report(batch: TextBatch):
    """
    Generate a comprehensive content report.
    """
    try:
        sentiment_results = analyze_sentiment(batch.texts)
        categorized_comments = categorize_comments(batch.texts)
        report = generate_content_report(
            transcription=batch.transcription,
            likes=batch.likes,
            dislikes=batch.dislikes,
            sentiment_results=sentiment_results,
            categorized_comments=categorized_comments
        )
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@sentiment_router.post("/export/json")
async def export_json(batch: TextBatch):
    """
    Export sentiment analysis to JSON.
    """
    try:
        sentiment_results = analyze_sentiment(batch.texts)
        return export_to_json(sentiment_results)
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting to JSON: {str(e)}")

@sentiment_router.post("/export/csv")
async def export_csv(batch: TextBatch):
    """
    Export sentiment analysis to CSV.
    """
    try:
        sentiment_results = analyze_sentiment(batch.texts)
        return export_to_csv(sentiment_results)
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting to CSV: {str(e)}")