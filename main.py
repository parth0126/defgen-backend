import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
HF_TOKEN = os.getenv("HF_TOKEN")

# Keywords for defence topic filter
INDIAN_DEFENCE_KEYWORDS = [
    "army", "navy", "air force", "drdo", "missile", "defence", "military", "soldier", "ssb", "agni",
    "brahmos", "tejas", "marcos", "raw", "iaf", "hal", "mod", "ncc", "nda", "cds", "para sf"
]

# Check if the question is about Indian defence
def is_defence_related(query: str) -> bool:
    query = query.lower()
    return any(keyword in query for keyword in INDIAN_DEFENCE_KEYWORDS)

# Filter valid, meaningful snippets only
def is_valid_snippet(snippet: str) -> bool:
    if not snippet:
        return False
    if "..." in snippet or len(snippet.split()) < 10:
        return False
    bad_tokens = ["recognise", "domestic", "doc", "timer", "666"]
    return not any(bad_token in snippet.lower() for bad_token in bad_tokens)

# Summarize using Hugging Face API
def summarize_text(snippets):
    combined_text = " ".join(snippets).strip()[:1024]
    if len(combined_text.split()) < 30:
        return "Sorry, there wasn't enough relevant content to generate a meaningful answer."

    url = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json={"inputs": combined_text})
        if response.status_code != 200:
            return f"[HF Error {response.status_code}]: {response.text}"
        result = response.json()
        return result[0]["summary_text"] if isinstance(result, list) else "[HF Error] Unexpected format"
    except Exception as e:
        return f"[HF Exception] {str(e)}"

# Query Google and extract valid snippets
def query_google(user_input):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=10"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])
        if not items:
            return "No search results found."

        snippets = [
            item.get("snippet", "").strip()
            for item in items
            if is_valid_snippet(item.get("snippet", ""))
        ][:5]

        if not snippets:
            return "Sorry, no clean information was found to generate an answer."

        return summarize_text(snippets)

    except Exception as e:
        return f"[Google Error] {str(e)}"

# Handle the chatbot query
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")

    try:
        if not is_defence_related(user_input):
            return {"response": "This question is out of my scope. I specialize in Indian defence topics."}
        response = query_google(user_input)
        return {"response": response}
    except Exception as e:
        return {"response": f"[Server Error] {str(e)}"}
