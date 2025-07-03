from typing import List, Dict, Optional
import os
from app.config import settings, MODEL_CONFIGS, get_log_config
import cohere
from transformers import pipeline, AutoTokenizer
from retry import retry
import logging.config
import re
import spacy
import emoji

# Suppress transformers warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

# Set up logging
logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

# Try importing spacy, with fallback if it fails
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("spaCy loaded successfully")
except Exception as e:
    logger.error(f"spaCy import or model loading failed: {e}")
    SPACY_AVAILABLE = False

# Initialize clients
try:
    model_config = MODEL_CONFIGS["sentiment"]
    tokenizer = AutoTokenizer.from_pretrained(model_config["model_name"], cache_dir=model_config["cache_dir"])
    sentiment_analyzer = pipeline("sentiment-analysis", model=model_config["model_name"], tokenizer=tokenizer)
    logger.info("Sentiment analyzer loaded successfully")
except Exception as e:
    logger.error(f"Failed to load sentiment analyzer: {e}")
    # Fallback to a simpler model
    try:
        model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=model_config["cache_dir"])
        sentiment_analyzer = pipeline("sentiment-analysis", model=model_name, tokenizer=tokenizer)
        logger.info("Fallback sentiment analyzer loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load fallback sentiment analyzer: {e}")
        raise

co = cohere.Client(settings.cohere_api_key)

def preprocess_text(text: str) -> str:
    """Convert emojis to text and handle invalid inputs."""
    if not isinstance(text, str) or not text.strip():
        return ""
    return emoji.demojize(text.strip())

def analyze_sentiment(texts: List[str], batch_size: int = 50) -> List[Dict[str, any]]:
    try:
        results = []
        valid_texts = [preprocess_text(text) for text in texts]
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            # Filter out empty strings
            non_empty_batch = [text for text in batch if text]
            empty_indices = [i + j for j, text in enumerate(batch) if not text]
            if non_empty_batch:
                truncated_batch = [tokenizer.decode(tokenizer.encode(text, max_length=settings.max_comment_length, truncation=True)) for text in non_empty_batch]
                for text, trunc_text in zip(non_empty_batch, truncated_batch):
                    if text != trunc_text:
                        logger.warning(f"Text truncated due to length: {text[:50]}...")
                batch_results = sentiment_analyzer(truncated_batch)
                for text, result in zip(non_empty_batch, batch_results):
                    sentiment = result["label"].capitalize()
                    confidence = round(result["score"], 2)
                    if confidence < 0.95:
                        sentiment = "Neutral"
                    results.append({
                        "text": text,
                        "sentiment": sentiment,
                        "confidence": confidence
                    })
            # Add default results for empty texts
            for idx in empty_indices:
                results.insert(idx, {
                    "text": texts[idx],
                    "sentiment": "Neutral",
                    "confidence": 0.5
                })
        # Ensure results match input length
        if len(results) != len(texts):
            logger.error(f"Sentiment results length {len(results)} does not match input length {len(texts)}")
            raise ValueError("Text alignment mismatch in sentiment analysis")
        return results
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}", exc_info=True)
        return [
            {
                "text": text,
                "sentiment": "Neutral",
                "confidence": 0.5
            }
            for text in texts
        ]

def extract_keywords(texts: List[str]) -> List[Dict[str, any]]:
    results = []
    for text in texts:
        processed_text = preprocess_text(text)
        keywords = []
        if processed_text and SPACY_AVAILABLE:
            try:
                doc = nlp(processed_text)
                keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "ADJ", "PROPN"] and not token.is_stop and not emoji.is_emoji(token.text)]
            except Exception as e:
                logger.error(f"Keyword extraction error for text '{text[:50]}...': {e}")
        results.append({"text": text, "keywords": keywords or ["car", "review"]})
    return results

def find_questions(texts: List[str]) -> List[Dict[str, any]]:
    question_words = r"^(why|what|when|where|who|how|is|are|does|do|did|can|could|should|would)\b.*\?$"
    results = []
    for text in texts:
        processed_text = preprocess_text(text)
        is_question = False
        if processed_text and SPACY_AVAILABLE:
            try:
                doc = nlp(processed_text)
                if any(token.text == "?" for token in doc):
                    is_question = True
                elif any(token.dep_ == "aux" and token.i == 0 for token in doc):
                    is_question = True
                elif re.match(question_words, processed_text.lower(), re.IGNORECASE):
                    is_question = True
            except Exception as e:
                logger.error(f"Question detection error for text '{text[:50]}...': {e}")
                is_question = "?" in processed_text or bool(re.match(question_words, processed_text.lower(), re.IGNORECASE))
        else:
            is_question = "?" in processed_text or bool(re.match(question_words, processed_text.lower(), re.IGNORECASE))
        results.append({"text": text, "is_question": is_question})
    return results

def categorize_comments(texts: List[str]) -> Dict[str, List[str]]:
    most_interesting = []
    hot_takes = []
    questions = []

    strong_words = {"best", "worst", "amazing", "terrible", "love", "hate", "fantastic", "awful", "superb", "disappointed", "leading", "dominate"}
    question_words = r"^(why|what|when|where|who|how|is|are|does|do|did|can|could|should|would)\b.*\?$"

    for text in texts:
        processed_text = preprocess_text(text)
        if processed_text and SPACY_AVAILABLE:
            try:
                doc = nlp(processed_text)
                if any(token.text == "?" for token in doc):
                    questions.append(text)
                    continue
                elif any(token.dep_ == "aux" and token.i == 0 for token in doc):
                    questions.append(text)
                    continue
                elif re.match(question_words, processed_text.lower(), re.IGNORECASE):
                    questions.append(text)
                    continue
            except Exception as e:
                logger.error(f"spaCy processing error for text '{text[:50]}...': {e}")
                if "?" in processed_text or bool(re.match(question_words, processed_text.lower(), re.IGNORECASE)):
                    questions.append(text)
                    continue
        else:
            if "?" in processed_text or bool(re.match(question_words, processed_text.lower(), re.IGNORECASE)):
                questions.append(text)
                continue

        try:
            sentiment = sentiment_analyzer(processed_text)[0]
            has_negation = False
            has_strong_language = False
            if processed_text and SPACY_AVAILABLE:
                try:
                    doc = nlp(processed_text)
                    has_negation = any(token.dep_ == "neg" for token in doc)
                    has_strong_language = any(token.text.lower() in strong_words for token in doc)
                except:
                    pass
            if sentiment["score"] > 0.9 or has_negation or has_strong_language:
                hot_takes.append(text)
                continue
        except Exception as e:
            logger.error(f"Sentiment analysis for categorization error: {e}")

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
    try:
        if transcription and len(transcription) > 1000:
            transcription = transcription[:1000] + "..."
            logger.warning("Transcription truncated to 1000 characters for Cohere processing")

        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for s in sentiment_results:
            sentiment_counts[s["sentiment"]] += 1
        total = sum(sentiment_counts.values())
        sentiment_summary = {k: (v / total * 100) if total > 0 else 0 for k, v in sentiment_counts.items()}

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
            model=settings.cohere_model,
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        summary = response.generations[0].text.strip()

        insights = []
        if sentiment_summary["Negative"] > 20:
            insights.append("Address negative feedback in future videos, e.g., clarify common complaints.")
        if len(categorized_comments["questions"]) > 0:
            insights.append("Create a FAQ video addressing viewer questions.")
        if sentiment_summary["Positive"] > 60:
            insights.append("Highlight popular features in future content to maintain engagement.")
        if not insights:
            insights.append("Review sentiment analysis and ensure all comments are processed correctly.")

        return {
            "summary": summary,
            "sentiment_summary": sentiment_summary,
            "categorized_comments": categorized_comments,
            "actionable_insights": insights
        }
    except Exception as e:
        logger.error(f"Cohere report generation error: {e}", exc_info=True)
        return {
            "summary": "Failed to generate report due to API error. Please check Cohere API key or network connection.",
            "sentiment_summary": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "categorized_comments": categorized_comments,
            "actionable_insights": ["Check Cohere API key and network connection, then retry."]
        }
    