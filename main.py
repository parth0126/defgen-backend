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

# Defence keywords list
INDIAN_DEFENCE_KEYWORDS = [
    "afspa", "agnipath", "agniveer", "akash", "arjun", "awacs", "bofors", "brahmos",
    "bsf", "capf", "cas", "cds", "coas", "cns", "csd", "crpf", "dac", "dcc", "dgqa",
    "drdo", "hal", "ins", "iaf", "idsa", "lca", "marcos", "mbt", "ncc", "nda", "nsg",
    "ofb", "para sf", "pinaka", "raw", "rdx", "rpf", "sam", "sar", "ssb", "spg",
    "tejas", "uav", "uas", "udhampur hq", "unpkf", "vikrant", "vikramaditya",
    "indian army", "indian navy", "indian air force", "parachute regiment",
    "missile", "defence", "armed forces", "sf", "commando", "field marshal",
    "general", "lieutenant general", "major general", "brigadier", "colonel",
    "major", "captain", "lieutenant", "subedar major", "subedar", "naib subedar",
    "havildar", "naik", "lance naik", "sepoy", "soldier", "admiral", "vice admiral",
    "rear admiral", "commodore", "commander", "lieutenant commander", "sub lieutenant",
    "midshipman", "marshal of the indian air force", "air chief marshal", "air marshal",
    "air vice marshal", "air commodore", "group captain", "wing commander",
    "squadron leader", "flight lieutenant", "flying officer", "scorpene submarine",
    "ins arihant", "project 75", "ins kalvari", "kilo class submarine", "nuclear submarine",
    "rafale", "mig 29", "sukhoi su 30", "hal dhruv", "netra awacs", "heron drone",
    "ghatak uav", "rudra helicopter", "nag", "trishul", "kali", "nirbhay", "barak", "astra"
]

# Check if the user input is related to Indian defence
def is_defence_related(query: str) -> bool:
    query = query.lower()
    return any(keyword in query for keyword in INDIAN_DEFENCE_KEYWORDS)

# Query Google and return up to 5000 words of snippets
def query_google(user_input):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=10"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])
        if not items:
            return "No search results found."

        # Collect snippets without exceeding 5000 words
        snippets = []
        word_count = 0
        max_words = 5000

        for item in items:
            snippet = item.get("snippet", "")
            words = snippet.split()
            if word_count + len(words) > max_words:
                remaining = max_words - word_count
                snippets.append(" ".join(words[:remaining]))
                break
            else:
                snippets.append(snippet)
                word_count += len(words)

        return "\n\n".join(snippets)

    except Exception as e:
        return f"[Error!] {str(e)}"

# FastAPI route to handle chatbot requests
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
