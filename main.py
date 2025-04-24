import os
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

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
HF_TOKEN = os.getenv("HF_TOKEN")

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def summarize_text(text):
    url = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    response = requests.post(url, headers=headers, json=payload)
    summary = response.json()
    if isinstance(summary, list) and "summary_text" in summary[0]:
        return summary[0]["summary_text"]
    return "Summary could not be generated."

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")

    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])
        if not items:
            return {"response": "No search results found."}

        query_embedding = embedder.encode(user_input, convert_to_tensor=True)
        snippets = []
        for item in items:
            snippet = item.get("snippet", "")
            if snippet:
                snippet_embedding = embedder.encode(snippet, convert_to_tensor=True)
                score = util.pytorch_cos_sim(query_embedding, snippet_embedding).item()
                snippets.append((score, snippet))

        top_snippets = [s for _, s in sorted(snippets, reverse=True)[:3]]
        combined_text = " ".join(top_snippets)[:1000]

        summary_text = summarize_text(combined_text)
        return {"response": summary_text}

    except Exception as e:
        return {"response": f"[Error] {str(e)}"}
