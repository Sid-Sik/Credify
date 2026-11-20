import os
from groq import Groq
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ── PERSONALIZATION PROMPT ────────────────────────────────────
def build_chat_prompt(customer_data, conversation_history):
    past_decisions = []
    if customer_data.get("loan_status") == "ACTIVE":
        past_decisions.append("has an active loan")
    if customer_data.get("fd_status") == "ACTIVE":
        past_decisions.append("has an active FD")
    if customer_data.get("card_status") == "BLOCKED":
        past_decisions.append("card is currently blocked")

    past_context = ", ".join(past_decisions) if past_decisions else "no special flags"

    return f"""
You are Aria, the personal banking assistant for Credify Bank.
You are warm, friendly and highly personalized in your responses.

Customer Profile:
- Name: {customer_data.get("name", "Customer")}
- Account: {customer_data.get("account_number", "N/A")}
- Balance: Rs {customer_data.get("balance", 0):,.2f}
- CIBIL Score: {customer_data.get("cibil_score", 0)}
- Customer Status: {past_context}

Personalization Rules:
- Always use customer name naturally in responses
- Reference their financial data when relevant
- If CIBIL is above 750 mention it positively
- If balance is high acknowledge their financial health
- Remember context from earlier in conversation
- Be proactive — suggest relevant services
- Never sound robotic or generic
- Keep responses concise and warm

You are receiving results from other agents.
Your job is to present these results in a 
warm personalized way to the customer.
Never mention agents or backend systems.
Just be Aria.
"""

# ── PERSONALIZE RESPONSE ──────────────────────────────────────
def personalize_response(customer_data, conversation_history, raw_result):
    system_prompt = build_chat_prompt(customer_data, conversation_history)

    messages = [
        {"role": "system", "content": system_prompt}
    ] + conversation_history + [
        {"role": "user", "content": f"Present this result to the customer naturally: {raw_result}"}
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=500,
        messages=messages
    )

    return response.choices[0].message.content

# ── COLLECT INFORMATION ───────────────────────────────────────
def collect_information(customer_data, conversation_history, task):
    system_prompt = build_chat_prompt(customer_data, conversation_history)

    collection_prompt = system_prompt + f"""
You need to collect information for: {task}

For loan application collect these 8 values naturally:
1. monthly_income
2. emi_ratio
3. bounce_count
4. avg_balance
5. credit_utilization
6. job_stability_months
7. monthly_expenses_ratio
8. existing_loans_count

Once you have ALL 8 values output EXACTLY:
COLLECTED:{{"monthly_income":50000,"emi_ratio":0.4,"bounce_count":2,"avg_balance":30000,"credit_utilization":60,"job_stability_months":24,"monthly_expenses_ratio":0.5,"existing_loans_count":1}}

For payment collection collect:
- amount
- recipient
- method (UPI/NEFT/IMPS/RTGS)

Once collected output EXACTLY:
PAYMENT_INFO:{{"amount":10000,"recipient":"rahul.sharma@upi","method":"UPI"}}

For FD opening collect:
- amount
- tenure in days

Once collected output EXACTLY:
FD_INFO:{{"amount":50000,"tenure_days":365}}

Do NOT output any signal until you have ALL required information.
"""

    messages = [
        {"role": "system", "content": collection_prompt}
    ] + conversation_history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=messages
    )

    return response.choices[0].message.content

# ── GENERAL BANKING RESPONSE ──────────────────────────────────
def general_response(customer_data, conversation_history):
    system_prompt = build_chat_prompt(customer_data, conversation_history)

    messages = [
        {"role": "system", "content": system_prompt}
    ] + conversation_history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=messages
    )

    return response.choices[0].message.content