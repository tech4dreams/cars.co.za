# cars.co.za

# 🚗 Cars.co.za Sentiment Analysis API (Backend)
 
This project is a **FastAPI backend** for automatically gathering, analyzing, and reporting on **public sentiment** from YouTube video comments (and soon Instagram posts/comments) for [Cars.co.za](https://www.cars.co.za/).
 
It enables the marketing/content team to:

- ✅ Understand audience sentiment

- ✅ Detect frequently asked questions

- ✅ Improve video content using feedback

- ✅ Generate reports based on real viewer insights
 
---
 
## 📦 Project Overview
 
**Goal:**  

Build a full-stack web app that:

- Fetches YouTube video comments

- Extracts video transcripts for context

- Analyzes sentiment (positive/neutral/negative)

- Highlights top keywords/questions

- Generates exportable reports (CSV, PDF, JSON)

- Visualizes data in a frontend dashboard (TBD)
 
---
 
## ⚙️ Tech Stack (Backend)
 
| Component     | Tech        |

|---------------|-------------|

| Web Framework | [FastAPI](https://fastapi.tiangolo.com) |

| YouTube API   | Google Data API v3 |

| Env Mgmt      | `python-dotenv` |

| NLP Service   | (Pluggable – Cohere / Hugging Face / OpenAI) |

| Runtime       | `uvicorn` (ASGI server) |
 
---
 
## 🚀 Setup Instructions
 
### ✅ 1. Clone the Repo
 
```bash

git clone https://github.com/yourusername/cars-sentiment-backend.git

cd cars-sentiment-backend

```
 
### ✅ 2. Create & Activate Virtual Environment
 
```bash

python -m venv venv

source venv/bin/activate  # Windows: venv\Scripts\activate

```
 
### ✅ 3. Install Dependencies
 
```bash

pip install -r requirements.txt

```
 
### ✅ 4. Add Your `.env` File
 
Create a `.env` file in the root of `app/`:
 
```

YOUTUBE_API_KEY=your_google_api_key_here

```
 
Get your API key here: https://console.cloud.google.com/apis/library/youtube.googleapis.com
 
> 💡 Don’t commit your `.env` file!
 
---
 
## 🏁 Running the App (Local Dev)
 
```bash

uvicorn app.main:app --reload

```
 
Go to:  

👉 http://127.0.0.1:8000/docs — for Swagger UI (auto-generated docs)
 
---
 
## 🧪 Available Endpoints
 
### 📥 `/youtube/comments`
 
Fetch top-level comments from a YouTube video.
 
**POST** `/youtube/comments`
 
```json

{

  "url": "https://www.youtube.com/watch?v=VIDEO_ID"

}

```
 
**Response:**

```json

{

  "video_id": "VIDEO_ID",

  "comments": [

    "This was super helpful!",

    "Why didn’t you compare the Fortuner?",

    ...

  ]

}

```
 
---
 
### 📊 `/analyze/sentiment`
 
Analyze a batch of comments (stubbed for now — integrates NLP models soon)
 
**POST** `/analyze/sentiment`
 
```json

{

  "texts": ["This car is awesome!", "I hate the camera angles."]

}

```
 
**Response:**

```json

[

  {

    "text": "This car is awesome!",

    "sentiment": "positive",

    "confidence": 0.97

  },

  ...

]

```
 
---
 
## 📁 Project Structure
 
```

cars-sentiment-backend/

│

├── app/

│   ├── main.py                # App entry point

│   ├── youtube.py             # YouTube API routes

│   ├── sentiment.py           # Sentiment API routes

│   ├── schemas.py             # Pydantic request/response models

│   ├── config.py              # Env loader (optional)

│   └── services/

│       ├── youtube_service.py # Fetches YouTube comments

│       ├── nlp_service.py     # Handles sentiment logic

│       └── utils.py           # Helpers (extract video ID, etc.)

│

├── requirements.txt

└── README.md

```
 
---
 
## 🛠️ Upcoming Features
 
- [ ] YouTube transcript extraction using `youtube-transcript-api`

- [ ] Instagram comment scraping via Meta Graph API

- [ ] Integration with real NLP (Cohere, OpenAI, or Hugging Face)

- [ ] PDF/CSV/JSON report generation

- [ ] Frontend dashboard with graphs and filters

- [ ] Historical sentiment tracking (optional DB)
 
---
 
## 🤝 Collaboration Notes
 
- Use `main` or `dev` branch for stable features.

- Create PRs for new modules (e.g., `/report`, `/instagram`)

- Keep code modular — every service in its own file

- Don’t commit `.env` or API keys

- Use VS Code Live Share if pair-programming
 
---
 
## 👥 Team
 
- **Tofiek Sasman** (Python backend dev)

- **[Teammate Name]** (Full-stack dev)
 
---
 
## 📞 Support
 
If you get stuck:

- Read the FastAPI docs: https://fastapi.tiangolo.com

- Use Postman or Swagger UI to test endpoints

- Check API quotas on Google Console

- Or ping your teammate 🙌
 
---
