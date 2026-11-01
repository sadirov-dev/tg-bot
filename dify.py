
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL")


def ask_dify(question: str, user_id: int, conversation_id: str | None = None):
    if not DIFY_API_KEY or not DIFY_BASE_URL:
        raise RuntimeError("Dify API settings are missing in .env")

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": {},
        "query": question,
        "response_mode": "blocking",
        "user": str(user_id),
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    response = requests.post(
        DIFY_BASE_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    result = response.json()

    return {
        "text": result.get("answer", ""),
        "conversation_id": result.get("conversation_id"),
    }
