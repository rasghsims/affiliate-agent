import os
import requests

API_KEY = os.environ["OPENROUTER_API_KEY"]

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "openrouter/free",
        "messages": [
            {
                "role": "user",
                "content": "Say exactly: Qwen agent is working."
            }
        ],
    },
    timeout=60,
)

response.raise_for_status()

print(response.json()["choices"][0]["message"]["content"])
