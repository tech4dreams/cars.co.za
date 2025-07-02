# Entry point
from fastapi import FastAPI
from app.sentiment import router as sentiment_router
from app.youtube import router as youtube_router

app = FastAPI()
app.include_router(sentiment_router, prefix="/analyze")
app.include_router(youtube_router, prefix="/youtube")