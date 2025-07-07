# Lightweight NLP service using only cloud APIs
# app/services/nlp_service.py (deployment version)

import os
import cohere
import traceback
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

# Initialize Cohere client
try:
    co = cohere.Client(os.getenv("COHERE_API_KEY"))
    print("✅ Cohere client initialized successfully")
except Exception as e:
    print(f"❌ Warning: Could not initialize Cohere client: {e}")
    co = None

def analyze_sentiment(comments: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze sentiment using Cohere's API instead of local models
    """
    if not co:
        return [{"text": comment, "label": "Unknown", "score": 0.0, "error": "Cohere API not available"} for comment in comments]
    
    results = []
    batch_size = 20  # Process in batches to avoid rate limits
    
    for i in range(0, len(comments), batch_size):
        batch = comments[i:i + batch_size]
        
        try:
            # Create a prompt for batch sentiment analysis
            comments_text = "\n".join([f"{idx+1}. {comment}" for idx, comment in enumerate(batch)])
            
            prompt = f"""
Analyze the sentiment of these comments. For each comment, respond with just the number, sentiment (POSITIVE/NEGATIVE/NEUTRAL), and confidence score (0-1).

Comments:
{comments_text}

Format your response like:
1. POSITIVE, 0.85
2. NEGATIVE, 0.92
3. NEUTRAL, 0.76

Response:"""

            response = co.chat(
                model="command-r",
                message=prompt,
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=1000
            )
            
            # Parse the response
            lines = response.text.strip().split('\n')
            
            for idx, line in enumerate(lines):
                if idx >= len(batch):
                    break
                    
                try:
                    # Parse format: "1. POSITIVE, 0.85"
                    parts = line.split(', ')
                    if len(parts) >= 2:
                        sentiment = parts[0].split('. ')[1].strip()
                        confidence = float(parts[1].strip())
                        
                        results.append({
                            "text": batch[idx],
                            "label": sentiment,
                            "score": round(confidence, 4)
                        })
                    else:
                        # Fallback parsing
                        results.append({
                            "text": batch[idx],
                            "label": "NEUTRAL",
                            "score": 0.5,
                            "error": "Parse error"
                        })
                except Exception as parse_error:
                    results.append({
                        "text": batch[idx],
                        "label": "NEUTRAL",
                        "score": 0.5,
                        "error": f"Parse error: {str(parse_error)}"
                    })
        
        except Exception as e:
            print(f"Error in sentiment analysis batch: {e}")
            # Add error results for the entire batch
            for comment in batch:
                results.append({
                    "text": comment,
                    "label": "Unknown",
                    "score": 0.0,
                    "error": str(e)
                })
    
    return results

def analyze_sentiment_simple(comments: List[str]) -> List[Dict[str, Any]]:
    """
    Simple rule-based sentiment analysis as fallback
    """
    results = []
    
    positive_words = ['good', 'great', 'amazing', 'awesome', 'excellent', 'love', 'best', 'fantastic', 'wonderful', '😊', '❤️', '👍', '🔥']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'sucks', 'disappointed', '😞', '👎', '💩']
    
    for comment in comments:
        if not comment or len(comment.strip()) < 3:
            results.append({
                "text": comment,
                "label": "NEUTRAL",
                "score": 0.5,
                "error": "Comment too short"
            })
            continue
        
        comment_lower = comment.lower()
        
        positive_count = sum(1 for word in positive_words if word in comment_lower)
        negative_count = sum(1 for word in negative_words if word in comment_lower)
        
        if positive_count > negative_count:
            label = "POSITIVE"
            score = min(0.6 + (positive_count * 0.1), 0.95)
        elif negative_count > positive_count:
            label = "NEGATIVE"
            score = min(0.6 + (negative_count * 0.1), 0.95)
        else:
            label = "NEUTRAL"
            score = 0.5
        
        results.append({
            "text": comment,
            "label": label,
            "score": round(score, 4)
        })
    
    return results

def categorize_comments(comments: List[str]) -> Dict[str, List[str]]:
    """
    Categorize comments using improved rules
    """
    interesting, hot_takes, questions = [], [], []
    
    for comment in comments:
        if not comment or len(comment.strip()) < 3:
            continue
            
        comment_lower = comment.lower()
        
        # Questions
        if ("?" in comment or 
            any(word in comment_lower for word in ["what", "why", "how", "where", "when", "which", "who", "can you", "could you", "would you"])):
            questions.append(comment)
        
        # Hot takes (strong opinions)
        elif (any(word in comment_lower for word in ["hate", "love", "best", "worst", "terrible", "amazing", "awesome", "sucks", "fire", "🔥", "💯"]) or
              len([c for c in comment if c.isupper()]) > len(comment) * 0.3):  # Lots of caps
            hot_takes.append(comment)
        
        # Interesting (longer, detailed comments)
        elif len(comment.split()) > 15:
            interesting.append(comment)
    
    return {
        "most_interesting": interesting[:10],
        "hot_takes": hot_takes[:10],
        "questions": questions[:10]
    }

def generate_report(transcript: str, sentiment_summary: List[Dict], likes: int, dislikes: int, categorized: Dict) -> str:
    """
    Generate report using Cohere API
    """
    if not co:
        return generate_simple_report(sentiment_summary, likes, dislikes, categorized)
    
    # Calculate sentiment overview
    sentiment_overview = {
        "positive": sum(1 for r in sentiment_summary if r["label"].upper() == "POSITIVE"),
        "neutral": sum(1 for r in sentiment_summary if r["label"].upper() == "NEUTRAL"),
        "negative": sum(1 for r in sentiment_summary if r["label"].upper() == "NEGATIVE")
    }
    
    total_comments = len(sentiment_summary)
    
    # Safely truncate transcript
    transcript_snippet = transcript[:800] if transcript else "No transcript available"
    
    # Sample of comments for context
    sample_comments = {
        "positive": [r["text"] for r in sentiment_summary if r["label"].upper() == "POSITIVE"][:3],
        "negative": [r["text"] for r in sentiment_summary if r["label"].upper() == "NEGATIVE"][:3],
        "questions": categorized.get("questions", [])[:3]
    }
    
    prompt = f"""
Create a professional video analysis report based on the following data:

VIDEO TRANSCRIPT SNIPPET:
{transcript_snippet}

ENGAGEMENT METRICS:
- Likes: {likes:,}
- Dislikes: {dislikes:,}
- Total Comments Analyzed: {total_comments:,}

SENTIMENT BREAKDOWN:
- Positive: {sentiment_overview['positive']} ({sentiment_overview['positive']/total_comments*100:.1f}%)
- Neutral: {sentiment_overview['neutral']} ({sentiment_overview['neutral']/total_comments*100:.1f}%)
- Negative: {sentiment_overview['negative']} ({sentiment_overview['negative']/total_comments*100:.1f}%)

SAMPLE POSITIVE COMMENTS:
{chr(10).join(sample_comments["positive"])}

SAMPLE NEGATIVE COMMENTS:
{chr(10).join(sample_comments["negative"])}

TOP VIEWER QUESTIONS:
{chr(10).join(sample_comments["questions"])}

Please write a concise professional report (250-300 words) that:
1. Summarizes the overall audience reception
2. Highlights key insights from the sentiment analysis
3. Identifies main themes in viewer feedback
4. Provides 2-3 actionable recommendations for future content

Format as a business report for the Cars.co.za content team.
"""
    
    try:
        response = co.chat(
            model="command-r",
            message=prompt,
            temperature=0.7,
            max_tokens=500
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error during report generation: {e}")
        traceback.print_exc()
        return generate_simple_report(sentiment_summary, likes, dislikes, categorized)

def generate_simple_report(sentiment_summary: List[Dict], likes: int, dislikes: int, categorized: Dict) -> str:
    """
    Generate a simple report without AI when Cohere is unavailable
    """
    total_comments = len(sentiment_summary)
    positive = sum(1 for r in sentiment_summary if r["label"].upper() == "POSITIVE")
    negative = sum(1 for r in sentiment_summary if r["label"].upper() == "NEGATIVE")
    neutral = sum(1 for r in sentiment_summary if r["label"].upper() == "NEUTRAL")
    
    positive_pct = (positive / total_comments * 100) if total_comments > 0 else 0
    negative_pct = (negative / total_comments * 100) if total_comments > 0 else 0
    
    report = f"""
VIDEO ANALYSIS REPORT

ENGAGEMENT OVERVIEW:
- Video Likes: {likes:,}
- Video Dislikes: {dislikes:,}
- Comments Analyzed: {total_comments:,}

SENTIMENT ANALYSIS:
- Positive Sentiment: {positive} comments ({positive_pct:.1f}%)
- Negative Sentiment: {negative} comments ({negative_pct:.1f}%)
- Neutral Sentiment: {neutral} comments ({(100-positive_pct-negative_pct):.1f}%)

AUDIENCE ENGAGEMENT:
- Questions from Viewers: {len(categorized.get('questions', []))}
- Hot Takes/Strong Opinions: {len(categorized.get('hot_takes', []))}
- Detailed Comments: {len(categorized.get('most_interesting', []))}

KEY INSIGHTS:
- Overall sentiment is {"positive" if positive_pct > 50 else "mixed" if positive_pct > 30 else "negative"}
- Engagement level: {"High" if total_comments > 50 else "Moderate" if total_comments > 20 else "Low"}
- Viewer questions indicate {"strong" if len(categorized.get('questions', [])) > 10 else "moderate"} interest

RECOMMENDATIONS:
1. {"Continue current content strategy" if positive_pct > 60 else "Address viewer concerns mentioned in negative feedback"}
2. {"Engage with viewer questions" if len(categorized.get('questions', [])) > 5 else "Encourage more viewer interaction"}
3. {"Capitalize on positive reception" if positive_pct > 50 else "Improve content based on feedback"}
"""
    
    return report.strip()

# Fallback function if Cohere fails
def get_fallback_analysis(comments: List[str]) -> List[Dict[str, Any]]:
    """Use simple rule-based analysis if all else fails"""
    return analyze_sentiment_simple(comments)