# app/main.py
from fastapi import FastAPI
from app.sentiment import sentiment_router

app = FastAPI(title="Cars Sentiment Backend", version="0.1.0")

app.include_router(sentiment_router, prefix="/analyze")

@app.get("/")
async def root():
    return {"message": "Welcome to Cars Sentiment Backend"}