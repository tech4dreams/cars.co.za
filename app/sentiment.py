import traceback
from fastapi import APIRouter, HTTPException
from app.schemas import AnalyzeVideoRequest, AnalyzeVideoResponse, YouTubeMetadataResponse, CommentCategories
from app.services import youtube_service, nlp_service

router = APIRouter()

@router.post("/video", response_model=AnalyzeVideoResponse)
async def analyze_video(data: AnalyzeVideoRequest):
    # Improved video ID extraction
    video_id = None
    if "v=" in data.video_url:
        video_id = data.video_url.split("v=")[-1][:11]
    elif "youtu.be/" in data.video_url:
        video_id = data.video_url.split("youtu.be/")[-1][:11]
    
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        # Fetch engagement data
        comments = youtube_service.get_video_comments(video_id)
        metadata = youtube_service.get_video_metadata(video_id)
        likes = metadata.get("likeCount", 0)
        dislikes = metadata.get("dislikeCount", 0)  # fallback to 0 if missing
        
        # Get transcript (handle if it fails)
        transcript = ""
        try:
            transcript = youtube_service.get_video_transcript(video_id)
        except Exception as transcript_error:
            print(f"Warning: Could not get transcript: {transcript_error}")
            transcript = "Transcript not available"
        
        # Run NLP tasks
        sentiment_results = nlp_service.analyze_sentiment(comments)
        categories = nlp_service.categorize_comments(comments)
        report = nlp_service.generate_report(transcript, sentiment_results, likes, dislikes, categories)

        return AnalyzeVideoResponse(
            video_id=video_id,
            sentiment_results=sentiment_results,
            categories=CommentCategories(**categories),  # Ensure proper instantiation
            report=report,
            metadata=YouTubeMetadataResponse(**metadata)
        )

    except Exception as e:
        print("🚨 ERROR in analyze_video endpoint:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")