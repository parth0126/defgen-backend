import os
import re
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV VARIABLES
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
HF_TOKEN = os.getenv("HF_TOKEN")

# Load sentence transformer for snippet ranking
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Hugging Face summarizer via Inference API
def summarize_text(text):
    if len(text) < 100:
        return "Not enough context to summarize."

    url = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": text}

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return f"[HF Error] Status {response.status_code}: {response.text}"

        result = response.json()

        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return "[HF Error] No summary_text found in response."

    except Exception as e:
        return f"[HF Exception] {str(e)}"

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")

    try:
        # Step 1: Google Custom Search
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])

        if not items:
            return {"response": "No search results found."}

        # Step 2: Snippet ranking using sentence similarity
        query_embedding = embedder.encode(user_input, convert_to_tensor=True)
        snippets = []

        for item in items:
            snippet = item.get("snippet", "")
            if not snippet:
                continue
            snippet_embedding = embedder.encode(snippet, convert_to_tensor=True)
            score = util.pytorch_cos_sim(query_embedding, snippet_embedding).item()
            snippets.append((score, snippet))

        # Step 3: Use top 2 relevant snippets
        top_snippets = [s for _, s in sorted(snippets, reverse=True)[:2]]

        # Step 4: Clean and combine text
        combined_text = " ".join(top_snippets)
        combined_text = re.sub(r"[^a-zA-Z0-9 .,:;\'\"!?-]", "", combined_text)
        combined_text = combined_text[:1000]  # truncate for safety

        # Step 5: Summarize
        summary_text = summarize_text(combined_text)
        return {"response": summary_text}

    except Exception as e:
        return {"response": f"[Server Error] {str(e)}"}
