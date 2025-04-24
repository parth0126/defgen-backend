import os
import re
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util

# ========== Load Environment Variables ==========
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
HF_TOKEN = os.getenv("HF_TOKEN")

# Debugging output
print(f"GOOGLE_API_KEY: {bool(GOOGLE_API_KEY)}")
print(f"GOOGLE_CX: {bool(GOOGLE_CX)}")
print(f"HF_TOKEN: {bool(HF_TOKEN)}")

# ========== Initialize FastAPI ==========
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Load Sentence Transformer ==========
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ========== Summarization Function ==========
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
        print("[DEBUG] HF status code:", response.status_code)
        print("[DEBUG] HF raw response:", response.text[:300])

        if response.status_code != 200:
            return f"[HF Error {response.status_code}] {response.text}"

        try:
            result = response.json()
        except ValueError:
            return f"[HF Error] Invalid JSON: {response.text}"

        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return "[HF Error] Unexpected response format."

    except Exception as e:
        return f"[HF Exception] {str(e)}"

# ========== Main Chat Endpoint ==========
@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_input = data.get("message", "").strip()

        if not user_input:
            return {"response": "❌ Please provide a valid query."}

        # Step 1: Google Search
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        if res.status_code != 200:
            return {"response": f"[Google Error {res.status_code}] {res.text}"}
        search_data = res.json()
        items = search_data.get("items", [])

        if not items:
            return {"response": "No search results found."}

        # Step 2: Rank Snippets
        query_embedding = embedder.encode(user_input, convert_to_tensor=True)
        ranked_snippets = []

        for item in items:
            snippet = item.get("snippet", "")
            if not snippet:
                continue
            snippet_embedding = embedder.encode(snippet, convert_to_tensor=True)
            score = util.pytorch_cos_sim(query_embedding, snippet_embedding).item()
            ranked_snippets.append((score, snippet))

        if not ranked_snippets:
            return {"response": "No relevant text to summarize from search results."}

        # Step 3: Combine top snippets
        top_snippets = [s for _, s in sorted(ranked_snippets, reverse=True)[:2]]
        combined_text = " ".join(top_snippets)
        combined_text = re.sub(r"[^a-zA-Z0-9 .,:;\'\"!?-]", "", combined_text)
        combined_text = combined_text[:1000]

        # Step 4: Summarize
        summary = summarize_text(combined_text)
        return {"response": summary}

    except Exception as e:
        return {"response": f"[Server Error] {str(e)}"}
