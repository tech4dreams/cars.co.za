# call to sentiment API

# app/services/nlp_service.py

import os
import cohere
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

# Sentiment Model (Hugging Face)
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)

# Cohere client
co = cohere.Client(os.getenv("COHERE_API_KEY"))

def analyze_sentiment(comments: list[str]) -> list[dict]:
    results = []
    for comment in comments:
        try:
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
        lowered = c.lower()
        if "?" in c or any(w in lowered for w in ["what", "why", "how"]):
            questions.append(c)
        elif any(w in lowered for w in ["i hate", "this sucks", "amazing", "this rules", "🔥"]):
            hot_takes.append(c)
        elif len(c.split()) > 12:
            interesting.append(c)
    return {
        "most_interesting": interesting,
        "hot_takes": hot_takes,
        "questions": questions
    }

def generate_report(transcript: str, sentiment_summary: list[dict], likes: int, dislikes: int, categorized: dict) -> str:
    sentiment_overview = {
        "positive": sum(1 for r in sentiment_summary if r["label"].lower() == "positive"),
        "neutral": sum(1 for r in sentiment_summary if r["label"].lower() == "neutral"),
        "negative": sum(1 for r in sentiment_summary if r["label"].lower() == "negative")
    }

    prompt = f"""
Video Transcript:
{transcript[:1000]}...

Likes: {likes} | Dislikes: {dislikes}

Sentiment Summary:
Positive: {sentiment_overview['positive']}
Neutral: {sentiment_overview['neutral']}
Negative: {sentiment_overview['negative']}

Comment Highlights:
Interesting:
{categorized['most_interesting'][:3]}

Hot Takes:
{categorized['hot_takes'][:3]}

Questions:
{categorized['questions'][:3]}

Please write a professional report summarizing how viewers responded to this video.
Include suggestions for improvement.
"""

    response = co.chat(
        model="command-r",
        message=prompt,
        temperature=0.7
    )
    return response.text.strip()
