import os
import requests
from urllib.parse import urlparse
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

# Trusted Indian defence websites
TRUSTED_DEFENCE_DOMAINS = [
    "indiandefensenews.in",
    "idrw.org",
    "drdo.gov.in",
    "mod.gov.in",
    "hal-india.co.in",
    "ssbcrack.com",
    "defencexp.com",
    "livefistdefence.com",
    "defenceaviationpost.com",
    "defenceguru.co.in"
]

# Check if the URL belongs to a trusted defence source
def is_defence_source(url):
    try:
        domain = urlparse(url).netloc
        return any(trusted in domain for trusted in TRUSTED_DEFENCE_DOMAINS)
    except:
        return False

# Query Google CSE and return filtered defence snippets
def query_google(user_input):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])

        if not items:
            return "No Google search results found."

        # Filter snippets from only trusted sources
        filtered_snippets = [
            item.get("snippet", "")
            for item in items
            if is_defence_source(item.get("link", ""))
        ]

        if not filtered_snippets:
            return "This question is out of my scope. I specialize in Indian defence topics."

        return "\n\n".join(filtered_snippets[:3])

    except Exception as e:
        return f"[Google error] {str(e)}"

# FastAPI route to handle chatbot queries
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")

    try:
        response = query_google(user_input)
        return {"response": response}
    except Exception as e:
        return {"response": f"[Server Error] {str(e)}"}
