import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

openai.api_key = OPENAI_API_KEY

def query_openai(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"[OpenAI error] {str(e)}"

def query_google(user_input):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        res = requests.get(url)
        data = res.json()
        items = data.get("items", [])
        if not items:
            return "No Google search results found."
        result = "\n".join(f"- {item['title']}: {item['link']}" for item in items[:3])
        return f"Top Google search results:\n{result}"
    except Exception as e:
        return f"[Google error] {str(e)}"

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    response = query_openai(user_message)
    if "error" in response.lower():
        response = query_google(user_message)
    return {"response": response}
