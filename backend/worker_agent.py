import sqlite3
import math
import json
import random
from datetime import datetime
from helper_agent import (
    get_card_details,
    get_balance,
    get_fd_details,
    get_ml_parameters
)

DB_PATH = "credify.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# ── ML MODEL ──────────────────────────────────────────────────
weights = [-0.33984054423362736, 1.1717101389588829, 1.6879276286089038,
           -0.2960277263445141, 0.8747292330415741, -0.9385134269810018,
           0.4711343439806323, 0.7853401735488533]
bias = -1.0

def sigmoid(z):
    z = max(min(z, 500), -500)
    return 1 / (1 + math.exp(-z))

# ── TOOL 1: LOAN DECISION ─────────────────────────────────────
def process_loan_application(phone, values):
    features = [
        values["monthly_income"] / 100000,
        values["emi_ratio"],
        values["bounce_count"] / 10,
        values["avg_balance"] / 100000,
        values["credit_utilization"] / 100,
        values["job_stability_months"] / 120,
        values["monthly_expenses_ratio"],
        values["existing_loans_count"] / 10
    ]
    z = sum(features[k] * weights[k] for k in range(8)) + bias
    prob = sigmoid(z)
    decision = "REJECTED" if prob >= 0.5 else "APPROVED"

    # Save to database
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE users SET
        monthly_income=?, emi_ratio=?, bounce_count=?,
        avg_balance=?, credit_utilization=?, job_stability_months=?,
        monthly_expenses_ratio=?, existing_loans_count=?
        WHERE phone=?""",
        (values["monthly_income"], values["emi_ratio"],
         values["bounce_count"], values["avg_balance"],
         values["credit_utilization"], values["job_stability_months"],
         values["monthly_expenses_ratio"], values["existing_loans_count"],
         phone))
    conn.commit()
    conn.close()

    return {
        "decision": decision,
        "probability": round(prob, 4)
    }

# ── TOOL 2: BLOCK CARD ────────────────────────────────────────
def block_card(phone):
    card = get_card_details(phone)
    if not card:
        return {"success": False, "message": "Card not found"}
    if card["card_status"] == "BLOCKED":
        return {"success": False, "message": "Card is already blocked"}

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET card_status='BLOCKED' WHERE phone=?", (phone,))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "card_number": card["card_number"],
        "message": "Card blocked successfully"
    }

# ── TOOL 3: UNBLOCK CARD ──────────────────────────────────────
def unblock_card(phone):
    card = get_card_details(phone)
    if not card:
        return {"success": False, "message": "Card not found"}
    if card["card_status"] == "ACTIVE":
        return {"success": False, "message": "Card is already active"}

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET card_status='ACTIVE' WHERE phone=?", (phone,))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "card_number": card["card_number"],
        "message": "Card unblocked successfully"
    }

# ── TOOL 4: PROCESS PAYMENT ───────────────────────────────────
def process_payment(phone, amount, recipient, method):
    balance_data = get_balance(phone)
    if not balance_data:
        return {"success": False, "message": "Account not found"}

    current_balance = balance_data["balance"]

    if current_balance < amount:
        return {"success": False, "message": "Insufficient balance"}

    new_balance = current_balance - amount

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET balance=? WHERE phone=?", (new_balance, phone))
    c.execute("""INSERT INTO transactions 
        (phone, description, amount, type, date) 
        VALUES (?, ?, ?, ?, ?)""",
        (phone, f"{method} Transfer to {recipient}",
         amount, "DEBIT",
         datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "amount": amount,
        "recipient": recipient,
        "method": method,
        "new_balance": new_balance,
        "message": f"Successfully transferred Rs {amount} to {recipient} via {method}"
    }

# ── TOOL 5: OPEN FD ───────────────────────────────────────────
def open_fd(phone, amount, tenure_days):
    balance_data = get_balance(phone)
    if not balance_data:
        return {"success": False, "message": "Account not found"}

    if balance_data["balance"] < amount:
        return {"success": False, "message": "Insufficient balance"}

    interest_rate = round(random.uniform(5.0, 8.5), 2)
    maturity_date = datetime.now().strftime("%Y-%m-%d")
    new_balance = balance_data["balance"] - amount

    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE users SET 
        fd_amount=?, fd_maturity_date=?, 
        fd_interest_rate=?, fd_status='ACTIVE',
        balance=?
        WHERE phone=?""",
        (amount, maturity_date, interest_rate, new_balance, phone))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "fd_amount": amount,
        "interest_rate": interest_rate,
        "maturity_date": maturity_date,
        "new_balance": new_balance,
        "message": f"FD of Rs {amount} opened at {interest_rate}% interest"
    }

# ── TOOL 6: CLOSE FD ──────────────────────────────────────────
def close_fd(phone):
    fd = get_fd_details(phone)
    if not fd:
        return {"success": False, "message": "No FD found"}
    if fd["fd_status"] == "NONE":
        return {"success": False, "message": "No active FD found"}

    balance_data = get_balance(phone)
    maturity_amount = fd["fd_amount"] * (1 + fd["fd_interest_rate"] / 100)
    new_balance = balance_data["balance"] + maturity_amount

    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE users SET 
        fd_status='NONE', balance=?
        WHERE phone=?""",
        (new_balance, phone))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "maturity_amount": round(maturity_amount, 2),
        "new_balance": round(new_balance, 2),
        "message": f"FD closed. Rs {round(maturity_amount, 2)} credited to your account"
    }

# ── TOOL 7: SAVE CONVERSATION ─────────────────────────────────
def save_conversation(phone, conversation_history, decision="IN_PROGRESS"):
    session_id = str(random.randint(1000, 9999))
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO conversations 
        (session_id, phone, chat_history, loan_decision) 
        VALUES (?, ?, ?, ?)""",
        (session_id, phone, json.dumps(conversation_history), decision))
    conn.commit()
    conn.close()
    return {"session_id": session_id}
