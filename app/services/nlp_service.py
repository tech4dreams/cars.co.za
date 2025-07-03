# call to sentiment API

# app/services/nlp_service.py

import os
import cohere
import traceback
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

# Sentiment Model (Hugging Face)
try:
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment"
    )
except Exception as e:
    print(f"Warning: Could not load sentiment model: {e}")
    sentiment_pipeline = None

# Cohere client
try:
    co = cohere.Client(os.getenv("COHERE_API_KEY"))
except Exception as e:
    print(f"Warning: Could not initialize Cohere client: {e}")
    co = None

def analyze_sentiment(comments: list[str]) -> list[dict]:
    if not sentiment_pipeline:
        return [{"text": comment, "label": "Unknown", "score": 0.0, "error": "Model not available"} for comment in comments]
    
    results = []
    for comment in comments:
        try:
            # Handle empty or very short comments
            if not comment or len(comment.strip()) < 3:
                results.append({
                    "text": comment,
                    "label": "Unknown",
                    "score": 0.0,
                    "error": "Comment too short"
                })
                continue
                
            analysis = sentiment_pipeline(comment)[0]
            results.append({
                "text": comment,
                "label": analysis["label"],
                "score": round(analysis["score"], 4)
            })
        except Exception as e:
            results.append({
                "text": comment,
                "label": "Unknown",
                "score": 0.0,
                "error": str(e)
            })
    return results

def categorize_comments(comments: list[str]) -> dict:
    interesting, hot_takes, questions = [], [], []
    
    for c in comments:
        if not c or len(c.strip()) < 3:
            continue
            
        lowered = c.lower()
        if "?" in c or any(w in lowered for w in ["what", "why", "how", "where", "when"]):
            questions.append(c)
        elif any(w in lowered for w in ["i hate", "this sucks", "amazing", "this rules", "🔥", "fire", "terrible", "worst", "best"]):
            hot_takes.append(c)
        elif len(c.split()) > 12:
            interesting.append(c)
    
    return {
        "most_interesting": interesting[:10],  # Limit to avoid overwhelming
        "hot_takes": hot_takes[:10],
        "questions": questions[:10]
    }

def generate_report(transcript: str, sentiment_summary: list[dict], likes: int, dislikes: int, categorized: dict) -> str:
    if not co:
        return "Report generation unavailable: Cohere client not initialized"
    
    # Calculate sentiment overview
    sentiment_overview = {
        "positive": sum(1 for r in sentiment_summary if r["label"].lower() in ["positive", "label_2"]),
        "neutral": sum(1 for r in sentiment_summary if r["label"].lower() in ["neutral", "label_1"]),
        "negative": sum(1 for r in sentiment_summary if r["label"].lower() in ["negative", "label_0"])
    }

    # Safely truncate transcript
    transcript_snippet = transcript[:1000] if transcript else "No transcript available"

    prompt = f"""
Video Transcript:
{transcript_snippet}...

Engagement Metrics:
Likes: {likes} | Dislikes: {dislikes}

Sentiment Summary:
Positive: {sentiment_overview['positive']}
Neutral: {sentiment_overview['neutral']}
Negative: {sentiment_overview['negative']}

Comment Highlights:
Interesting Comments:
{categorized['most_interesting'][:3]}

Hot Takes:
{categorized['hot_takes'][:3]}

Questions from Viewers:
{categorized['questions'][:3]}

Please write a professional report summarizing how viewers responded to this video.
Include suggestions for improvement and key insights about audience engagement.
"""

    try:
        response = co.chat(
            model="command-r",
            message=prompt,
            temperature=0.7
        )
        return response.text.strip() if hasattr(response, 'text') else str(response)
    except Exception as e:
        print("Error during report generation:", e)
        traceback.print_exc()
        return f"Failed to generate report: {str(e)}"