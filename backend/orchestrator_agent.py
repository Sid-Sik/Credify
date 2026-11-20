import os
from groq import Groq
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ── CLASSIFY INTENT ───────────────────────────────────────────
def classify_intent(message):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""Classify this banking message into ONE word:
loan, account, card, payment, fd, investment, general

Message: "{message}"

Reply with ONLY the one word."""
        }]
    )
    return response.choices[0].message.content.strip().lower()

# ── ROUTE DECISION ────────────────────────────────────────────
def route_request(intent, message, customer_data):
    routing_map = {
        "loan": "collect_and_decide",
        "account": "fetch_and_respond",
        "card": "action_required",
        "payment": "collect_and_execute",
        "fd": "collect_and_execute",
        "investment": "fetch_and_respond",
        "general": "general_response"
    }

    action = routing_map.get(intent, "general_response")

    return {
        "intent": intent,
        "action": action,
        "message": message,
        "customer_data": customer_data
    }