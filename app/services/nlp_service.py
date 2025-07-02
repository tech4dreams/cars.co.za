from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import cohere
from transformers import pipeline
from retry import retry
import logging
import re

# Suppress transformers warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing spacy, with fallback if it fails
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("spaCy loaded successfully")
except Exception as e:
    logger.error(f"spaCy import or model loading failed: {e}")
    SPACY_AVAILABLE = False

# Load environment variables
load_dotenv("C:/Users/Seth.Valentine/cars.co.za/.env")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found in .env file")

# Initialize clients
try:
    sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    logger.info("Sentiment analyzer loaded successfully")
except Exception as e:
    logger.error(f"Failed to load sentiment analyzer: {e}")
    raise

co = cohere.Client(COHERE_API_KEY)

def analyze_sentiment(texts: List[str], batch_size: int = 50) -> List[Dict[str, any]]:
    """
    Perform sentiment analysis using HuggingFace's transformers with batch processing.
    Adds neutral sentiment for low-confidence predictions.
    """
    try:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = sentiment_analyzer(batch)
            for text, result in zip(batch, batch_results):
                sentiment = result["label"].capitalize()
                confidence = result["score"]
                # Label as Neutral if confidence is below 0.95
                if confidence < 0.95:
                    sentiment = "Neutral"
                results.append({
                    "text": text,
                    "sentiment": sentiment,
                    "confidence": confidence
                })
        return results
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return [
            {
                "text": text,
                "sentiment": "Neutral",
                "confidence": 0.5
            }
            for text in texts
        ]

def extract_keywords(texts: List[str]) -> List[Dict[str, any]]:
    """
    Extract keywords from texts using spaCy.
    """
    results = []
    for text in texts:
        keywords = []
        if SPACY_AVAILABLE:
            try:
                doc = nlp(text)
                keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop]
            except Exception as e:
                logger.error(f"Keyword extraction error: {e}")
        results.append({"text": text, "keywords": keywords or ["car", "review"]})
    return results

def find_questions(texts: List[str]) -> List[Dict[str, any]]:
    """
    Identify questions in texts using spaCy or heuristic.
    """
    question_words = r"^(why|what|when|where|who|how|is|are|does|do|did|can|could|should|would)\b"
    results = []
    for text in texts:
        is_question = False
        if SPACY_AVAILABLE:
            try:
                doc = nlp(text)
                # Check for question mark or question-like structure (auxiliary verb at start)
                if any(token.text == "?" for token in doc):
                    is_question = True
                elif any(token.dep_ == "aux" and token.i == 0 for token in doc):  # Auxiliary verb at sentence start
                    is_question = True
                # Check for question words at the start of the sentence
                elif re.match(question_words, text.lower(), re.IGNORECASE):
                    is_question = True
            except Exception as e:
                logger.error(f"Question detection error: {e}")
                is_question = "?" in text or bool(re.match(question_words, text.lower(), re.IGNORECASE))
        else:
            is_question = "?" in text or bool(re.match(question_words, text.lower(), re.IGNORECASE))
        results.append({"text": text, "is_question": is_question})
    return results

def categorize_comments(texts: List[str]) -> Dict[str, List[str]]:
    """
    Categorize comments into Most Interesting, Hot Takes, and Questions.
    """
    most_interesting = []
    hot_takes = []
    questions = []

    question_words = r"^(why|what|when|where|who|how|is|are|does|do|did|can|could|should|would)\b"
    for text in texts:
        # Questions: Use spaCy if available, else fallback to heuristic
        if SPACY_AVAILABLE:
            try:
                doc = nlp(text)
                if any(token.text == "?" for token in doc):
                    questions.append(text)
                    continue
                elif any(token.dep_ == "aux" and token.i == 0 for token in doc):
                    questions.append(text)
                    continue
                elif re.match(question_words, text.lower(), re.IGNORECASE):
                    questions.append(text)
                    continue
            except Exception as e:
                logger.error(f"spaCy processing error: {e}")
                if "?" in text or bool(re.match(question_words, text.lower(), re.IGNORECASE)):
                    questions.append(text)
                    continue
        else:
            if "?" in text or bool(re.match(question_words, text.lower(), re.IGNORECASE)):
                questions.append(text)
                continue

        # Hot Takes: Opinionated, strong sentiment, or controversial
        try:
            sentiment = sentiment_analyzer(text)[0]
            has_negation = False
            if SPACY_AVAILABLE:
                try:
                    doc = nlp(text)
                    has_negation = any(token.dep_ == "neg" for token in doc)
                except:
                    pass
            if sentiment["score"] > 0.9 or has_negation:
                hot_takes.append(text)
                continue
        except Exception as e:
            logger.error(f"Sentiment analysis for categorization error: {e}")

        # Most Interesting: Default for non-questions, non-hot-takes with moderate sentiment
        if 0.6 <= sentiment["score"] <= 0.9:
            most_interesting.append(text)

    return {
        "most_interesting": most_interesting,
        "hot_takes": hot_takes,
        "questions": questions
    }

@retry(tries=3, delay=1, backoff=2)
def generate_content_report(
    transcription: Optional[str],
    likes: int,
    dislikes: int,
    sentiment_results: List[Dict[str, any]],
    categorized_comments: Dict[str, List[str]]
) -> Dict[str, any]:
    """
    Generate a comprehensive report using Cohere.
    """
    try:
        # Calculate sentiment distribution
        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for s in sentiment_results:
            sentiment_counts[s["sentiment"]] += 1
        total = sum(sentiment_counts.values())
        sentiment_summary = {k: (v / total * 100) if total > 0 else 0 for k, v in sentiment_counts.items()}

        # Prepare prompt for Cohere
        prompt = f"""
        Generate a comprehensive report for a car review video with the following data:
        - Transcription: {transcription or 'Not provided'}
        - Likes: {likes}
        - Dislikes: {dislikes}
        - Sentiment Analysis: {sentiment_summary}
        - Categorized Comments:
          - Most Interesting: {', '.join(categorized_comments['most_interesting']) or 'None'}
          - Hot Takes: {', '.join(categorized_comments['hot_takes']) or 'None'}
          - Questions: {', '.join(categorized_comments['questions']) or 'None'}

        Summarize viewer sentiment and suggest actionable improvements for future content creation.
        """
        response = co.generate(
            model="command",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        summary = response.generations[0].text.strip()

        # Generate actionable insights
        insights = []
        if sentiment_summary["Negative"] > 20:
            insights.append("Address negative feedback in future videos, e.g., clarify common complaints.")
        if len(categorized_comments["questions"]) > 0:
            insights.append("Create a FAQ video addressing viewer questions.")
        if sentiment_summary["Positive"] > 60:
            insights.append("Highlight popular features in future content to maintain engagement.")

        return {
            "summary": summary,
            "sentiment_summary": sentiment_summary,
            "categorized_comments": categorized_comments,
            "actionable_insights": insights
        }
    except Exception as e:
        logger.error(f"Cohere report generation error: {e}")
        return {
            "summary": "Failed to generate report due to API error.",
            "sentiment_summary": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "categorized_comments": categorized_comments,
            "actionable_insights": ["Retry report generation or check API key."]
        }
    