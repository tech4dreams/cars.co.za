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

# Load spaCy with fallback
SPACY_AVAILABLE = False
nlp = None
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("spaCy loaded successfully")
except Exception as e:
    logger.error(f"spaCy import or model loading failed: {e}")

# Load environment variables
load_dotenv("C:/Users/Seth.Valentine/cars.co.za/.env")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found in .env file")

# Initialize cohere client
co = cohere.Client(COHERE_API_KEY)

# Lazy load sentiment analyzer
sentiment_analyzer = None
def get_sentiment_analyzer():
    global sentiment_analyzer
    if sentiment_analyzer is None:
        try:
            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                clean_up_tokenization_spaces=True
            )
            logger.info("Sentiment analyzer loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentiment analyzer: {e}")
            raise
    return sentiment_analyzer

def analyze_sentiment(texts: List[str], batch_size: int = 50) -> List[Dict[str, any]]:
    """
    Perform sentiment analysis with batch processing. Labels low-confidence predictions as Neutral.
    """
    try:
        analyzer = get_sentiment_analyzer()
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = analyzer(batch)
            for text, result in zip(batch, batch_results):
                sentiment = result["label"].capitalize()
                confidence = result["score"]
                if confidence < 0.95:
                    sentiment = "Neutral"
                results.append({"text": text, "sentiment": sentiment, "confidence": confidence})
        return results
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return [{"text": text, "sentiment": "Neutral", "confidence": 0.5} for text in texts]

def extract_keywords(texts: List[str]) -> List[Dict[str, any]]:
    """
    Extract keywords using spaCy or fallback to defaults.
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

def categorize_comments(texts: List[str]) -> Dict[str, List[str]]:
    """
    Categorize comments into Most Interesting, Hot Takes, and Questions.
    Also returns question detection results for consistency.
    """
    most_interesting = []
    hot_takes = []
    questions = []
    question_results = []
    question_words = r"^(why|what|when|where|who|how|is|are|does|do|did|can|could|should|would)\b"

    for text in texts:
        is_question = False
        if SPACY_AVAILABLE:
            try:
                doc = nlp(text)
                if any(token.text == "?" for token in doc) or \
                   any(token.dep_ == "aux" and token.i == 0 for token in doc) or \
                   re.match(question_words, text.lower(), re.IGNORECASE):
                    is_question = True
                    questions.append(text)
            except Exception as e:
                logger.error(f"spaCy processing error: {e}")
                is_question = "?" in text or bool(re.match(question_words, text.lower(), re.IGNORECASE))
        else:
            is_question = "?" in text or bool(re.match(question_words, text.lower(), re.IGNORECASE))
        
        question_results.append({"text": text, "is_question": is_question})
        
        if is_question:
            continue

        try:
            analyzer = get_sentiment_analyzer()
            sentiment = analyzer(text)[0]
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
            if 0.6 <= sentiment["score"] <= 0.9:
                most_interesting.append(text)
        except Exception as e:
            logger.error(f"Sentiment analysis for categorization error: {e}")
            most_interesting.append(text)  # Default to most_interesting on error

    return {
        "categorized": {
            "most_interesting": most_interesting,
            "hot_takes": hot_takes,
            "questions": questions
        },
        "questions": question_results
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
    Generate a report using Cohere with sentiment summary and insights.
    """
    try:
        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for s in sentiment_results:
            sentiment_counts[s["sentiment"]] += 1
        total = sum(sentiment_counts.values())
        sentiment_summary = {k: (v / total * 100) if total > 0 else 0 for k, v in sentiment_counts.items()}

        prompt = f"""
        Car review video report:
        - Transcription: {transcription or 'Not provided'}
        - Likes: {likes}, Dislikes: {dislikes}
        - Sentiment: {sentiment_summary}
        - Comments:
          - Most Interesting: {', '.join(categorized_comments['most_interesting']) or 'None'}
          - Hot Takes: {', '.join(categorized_comments['hot_takes']) or 'None'}
          - Questions: {', '.join(categorized_comments['questions']) or 'None'}
        Summarize sentiment and suggest improvements.
        """
        response = co.generate(model="command", prompt=prompt, max_tokens=500, temperature=0.7)
        summary = response.generations[0].text.strip()

        insights = []
        if sentiment_summary["Negative"] > 20:
            insights.append("Address negative feedback in future videos.")
        if len(categorized_comments["questions"]) > 0:
            insights.append("Create a FAQ video for viewer questions.")
        if sentiment_summary["Positive"] > 60:
            insights.append("Highlight popular features to maintain engagement.")

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
            "actionable_insights": ["Check API key and retry."]
        }
    