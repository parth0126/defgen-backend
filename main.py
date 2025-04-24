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

def is_defence_related(query: str) -> bool:
    query = query.lower()
    return any(keyword in query for keyword in INDIAN_DEFENCE_KEYWORDS)

def is_valid_snippet(snippet: str) -> bool:
    return snippet and "..." not in snippet and len(snippet.split()) >= 10

def summarize_with_phi2(snippets):
    combined_text = " ".join(snippets).strip()[:1024]
    if len(combined_text.split()) < 30:
        return "Sorry, there wasn't enough relevant content to generate a meaningful answer."

    prompt = f"Summarize this:\n\n{combined_text}\n\nSummary:"
    url = "https://api-inference.huggingface.co/models/microsoft/phi-2"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json={"inputs": prompt})
        if response.status_code != 200:
            return f"[Phi-2 Error {response.status_code}]: {response.text}"
        result = response.json()
        return result[0]["generated_text"].split("Summary:")[-1].strip() if isinstance(result, list) else "[Phi-2 Error] Unexpected response format"
    except Exception as e:
        return f"[Phi-2 Exception] {str(e)}"

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
            fallback = next((item.get("snippet") for item in items if item.get("snippet")), None)
            return f"(Fallback snippet)\n\n{fallback}" if fallback else "No useful information found."

        return summarize_with_phi2(snippets)

    except Exception as e:
        return f"[Google Error] {str(e)}"

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
