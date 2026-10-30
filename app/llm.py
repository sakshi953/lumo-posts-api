import json
import os

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_json(system: str, user: str) -> dict:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    resp = httpx.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return json.loads(resp.json()["choices"][0]["message"]["content"])
