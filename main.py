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

# List of Indian defence keywords
INDIAN_DEFENCE_KEYWORDS = [
    "indian army", "indian navy", "indian air force", "drdo", "ssb", "agni", "brahmos",
    "tejas", "marcos", "parachute regiment", "missile", "defence", "armed forces",
    "sf", "commando", "defence research", "military", "naval", "iaf", "hal", "mod"
]

def is_defence_related(query: str) -> bool:
    query = query.lower()
    return any(keyword in query for keyword in INDIAN_DEFENCE_KEYWORDS)

def query_google(user_input):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])
        if not items:
            return "No Google search results found."

        # Return only the snippet content
        result = "\n\n".join(
            f"{item.get('snippet', '')}"
            for item in items[:3]
        )
        return result
    except Exception as e:
        return f"[Google error] {str(e)}"

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
