from fastapi import APIRouter, HTTPException
from app.services.nlp_service import analyze_sentiment, extract_keywords, find_questions
from app.schemas import TextBatch
from app.config import get_log_config
import logging.config

logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

sentiment_router = APIRouter()

@sentiment_router.post("/sentiment")
async def analyze_comments(comment_data: TextBatch):
    try:
        # Validate input texts
        if not comment_data.texts:
            logger.warning("No comments provided for analysis")
            return []
        valid_texts = [text for text in comment_data.texts if isinstance(text, str) and text.strip()]
        if len(valid_texts) != len(comment_data.texts):
            logger.warning(f"Filtered {len(comment_data.texts) - len(valid_texts)} invalid or empty comments")
        
        sentiment_results = analyze_sentiment(comment_data.texts)
        keyword_results = extract_keywords(comment_data.texts)
        question_results = find_questions(comment_data.texts)

        # Verify alignment
        if not (len(sentiment_results) == len(keyword_results) == len(question_results) == len(comment_data.texts)):
            logger.error(f"Result length mismatch: sentiment={len(sentiment_results)}, keywords={len(keyword_results)}, questions={len(question_results)}, input={len(comment_data.texts)}")
            raise ValueError("Text alignment mismatch")

        return [
            {
                "text": text,
                "sentiment": sentiment["sentiment"],
                "confidence": sentiment["confidence"],
                "keywords": keywords["keywords"],
                "is_question": question["is_question"]
            }
            for text, sentiment, keywords, question in zip(
                comment_data.texts, sentiment_results, keyword_results, question_results
            )
        ]
    except Exception as e:
        logger.error(f"Error analyzing comments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing comments: {str(e)}")
    