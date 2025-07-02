from fastapi import APIRouter, HTTPException
from app.schemas import TextBatch, SentimentResponse, ReportResponse
from app.services.nlp_service import analyze_sentiment, extract_keywords, categorize_comments, generate_content_report
from app.services.youtube_service import fetch_youtube_data
from app.services.export_service import export_to_json, export_to_csv, export_to_pdf
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment_endpoint(payload: TextBatch):
    try:
        sentiment_results = analyze_sentiment(payload.texts)
        keywords = extract_keywords(payload.texts)
        categorized = categorize_comments(payload.texts)
        return {
            "sentiment": sentiment_results,
            "keywords": keywords,
            "questions": categorized["questions"]
        }
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(status_code=500, detail="Error processing sentiment analysis")

@router.post("/report", response_model=ReportResponse)
async def generate_report(payload: TextBatch):
    try:
        sentiment_results = analyze_sentiment(payload.texts)
        categorized = categorize_comments(payload.texts)
        report = generate_content_report(
            transcription=payload.transcription,
            likes=payload.likes,
            dislikes=payload.dislikes,
            sentiment_results=sentiment_results,
            categorized_comments=categorized["categorized"]
        )
        return report
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail="Error generating report")

@router.post("/export/json")
async def export_to_json_endpoint(payload: TextBatch):
    try:
        sentiment_results = analyze_sentiment(payload.texts)
        keywords = extract_keywords(payload.texts)
        categorized = categorize_comments(payload.texts)
        report = generate_content_report(
            transcription=payload.transcription,
            likes=payload.likes,
            dislikes=payload.dislikes,
            sentiment_results=sentiment_results,
            categorized_comments=categorized["categorized"]
        )
        filename = export_to_json({
            "sentiment": sentiment_results,
            "keywords": keywords,
            "questions": categorized["questions"],
            "report": report
        })
        return {"filename": filename}
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        raise HTTPException(status_code=500, detail="Error exporting to JSON")

@router.post("/export/csv")
async def export_to_csv_endpoint(payload: TextBatch):
    try:
        sentiment_results = analyze_sentiment(payload.texts)
        keywords = extract_keywords(payload.texts)
        categorized = categorize_comments(payload.texts)
        filename = export_to_csv({
            "sentiment": sentiment_results,
            "keywords": keywords,
            "questions": categorized["questions"]
        })
        return {"filename": filename}
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        raise HTTPException(status_code=500, detail="Error exporting to CSV")

@router.post("/export/pdf")
async def export_to_pdf_endpoint(payload: TextBatch):
    try:
        sentiment_results = analyze_sentiment(payload.texts)
        keywords = extract_keywords(payload.texts)
        categorized = categorize_comments(payload.texts)
        report = generate_content_report(
            transcription=payload.transcription,
            likes=payload.likes,
            dislikes=payload.dislikes,
            sentiment_results=sentiment_results,
            categorized_comments=categorized["categorized"]
        )
        filename = export_to_pdf({
            "sentiment": sentiment_results,
            "keywords": keywords,
            "questions": categorized["questions"],
            "report": report
        })
        return {"filename": filename}
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail="Error exporting to PDF")

@router.post("/full-report")
async def generate_full_report(url: str):
    """
    Generate a full analysis report from a YouTube URL, including sentiment, categorization,
    report, and exports to JSON, CSV, and PDF.
    """
    try:
        # Fetch YouTube data
        youtube_data = fetch_youtube_data(url)
        metadata = youtube_data["metadata"]
        comments = youtube_data["comments"]
        transcript = youtube_data["transcript"]

        # Combine all text for analysis
        texts = comments + [transcript] if transcript else comments
        if not texts:
            raise ValueError("No comments or transcript available for analysis")

        # Perform analysis
        sentiment_results = analyze_sentiment(texts)
        keywords = extract_keywords(texts)
        categorized = categorize_comments(texts)
        report = generate_content_report(
            transcription=transcript,
            likes=metadata["like_count"],
            dislikes=metadata["dislike_count"],
            sentiment_results=sentiment_results,
            categorized_comments=categorized["categorized"]
        )

        # Export results
        full_data = {
            "metadata": metadata,
            "sentiment": sentiment_results,
            "keywords": keywords,
            "questions": categorized["questions"],
            "report": report
        }
        json_filename = export_to_json(full_data)
        csv_filename = export_to_csv(full_data)
        pdf_filename = export_to_pdf(full_data)

        return {
            "metadata": metadata,
            "analysis": {
                "sentiment": sentiment_results,
                "keywords": keywords,
                "questions": categorized["questions"]
            },
            "report": report,
            "exports": {
                "json": json_filename,
                "csv": csv_filename,
                "pdf": pdf_filename
            }
        }
    except Exception as e:
        logger.error(f"Full report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating full report: {str(e)}")