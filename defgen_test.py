import requests

url = "https://defgen-backend.onrender.com/chat"
payload = {"message": "Tell me about Indian Army MARCOS"}
res = requests.post(url, json=payload)

print("Status:", res.status_code)
print("Output:", res.json())
