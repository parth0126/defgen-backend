import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# Load models
embedder = SentenceTransformer('all-MiniLM-L6-v2')
summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small")

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    
    try:
        # Google Search API request
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])
        
        if not items:
            return {"response": "No results found."}

        query_embedding = embedder.encode(user_input, convert_to_tensor=True)
        scored_snippets = []

        for item in items:
            snippet = item.get("snippet", "")
            if not snippet:
                continue
            snippet_embedding = embedder.encode(snippet, convert_to_tensor=True)
            score = util.pytorch_cos_sim(query_embedding, snippet_embedding).item()
            scored_snippets.append((score, snippet))

        # Sort and pick top 3 most relevant snippets
        top_snippets = [s for _, s in sorted(scored_snippets, reverse=True)[:3]]
        combined_text = " ".join(top_snippets)[:1000]  # Limit to safe input length

        # Summarize
        summary = summarizer(combined_text, max_length=100, min_length=30, do_sample=False)
        return {"response": summary[0]['summary_text']}
    
    except Exception as e:
        return {"response": f"[Error] {str(e)}"}
