import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import logging

logger = logging.getLogger(__name__)

def export_to_json(data: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Export analysis results to a JSON file.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/sentiment_results_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported JSON to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise

def export_to_csv(data: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Export analysis results to a CSV file.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/sentiment_results_{timestamp}.csv"

        # Flatten data for CSV
        sentiment_data = data.get("sentiment", [])
        keywords_data = data.get("keywords", [])
        questions_data = data.get("questions", [])

        rows = []
        for s, k, q in zip(sentiment_data, keywords_data, questions_data):
            row = {
                "text": s["text"],
                "sentiment": s["sentiment"],
                "confidence": s["confidence"],
                "keywords": ", ".join(k["keywords"]),
                "is_question": q["is_question"]
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False, encoding="utf-8")
        logger.info(f"Exported CSV to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise

def export_to_pdf(data: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Export analysis results to a PDF file.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/sentiment_results_{timestamp}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Sentiment Analysis Report", styles["Title"]))
        story.append(Spacer(1, 12))

        # Sentiment Summary
        sentiment_summary = data.get("sentiment_summary", {})
        story.append(Paragraph("Sentiment Summary", styles["Heading2"]))
        for sentiment, percentage in sentiment_summary.items():
            story.append(Paragraph(f"{sentiment}: {percentage:.2f}%", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Categorized Comments
        categorized = data.get("categorized_comments", {})
        for category, comments in categorized.items():
            story.append(Paragraph(category.replace("_", " ").title(), styles["Heading2"]))
            for comment in comments:
                story.append(Paragraph(comment, styles["Normal"]))
            story.append(Spacer(1, 12))

        # Actionable Insights
        insights = data.get("actionable_insights", [])
        story.append(Paragraph("Actionable Insights", styles["Heading2"]))
        for insight in insights:
            story.append(Paragraph(f"- {insight}", styles["Normal"]))

        doc.build(story)
        logger.info(f"Exported PDF to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        raise