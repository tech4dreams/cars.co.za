# Entry point

from fastapi import FastAPI
from app.youtube import router as youtube_router
from app.sentiment import router as sentiment_router
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Cars.co.za Sentiment API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
app.include_router(sentiment_router, prefix="/analyze", tags=["Sentiment"])