import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import math
import json
import random
import sqlite3
from datetime import datetime, timedelta
from chat_agent import personalize_response, collect_information, general_response
from orchestrator_agent import classify_intent, route_request
from agent import run_agent
from worker_agent import save_conversation
from worker_agent import (
    process_loan_application,
    block_card,
    unblock_card,
    process_payment,
    open_fd,
    close_fd,
    save_conversation
)
from helper_agent import (
    get_user_profile,
    get_account_details,
    get_investment_details,
    get_card_details,
    get_balance,
    get_transactions,
    get_loan_details,
    get_fd_details,
    get_cibil_details
)
app = Flask(__name__)
CORS(app)

# GROQ CLIENT
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# DATABASE SETUP
def init_db():
    conn = sqlite3.connect("credify.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY,
        otp TEXT,
        name TEXT,
        pan TEXT,
        customer_type TEXT DEFAULT "NEW",
        account_number TEXT,
        account_type TEXT,
        balance REAL,
        branch TEXT,
        card_number TEXT,
        card_type TEXT,
        card_status TEXT DEFAULT "ACTIVE",
        cibil_score INTEGER,
        outstanding_emi INTEGER,
        loan_amount REAL,
        loan_status TEXT,
        loan_emi REAL,
        loan_tenure INTEGER,
        fd_amount REAL,
        fd_maturity_date TEXT,
        fd_interest_rate REAL,
        fd_status TEXT,
        mutual_fund_value REAL,
        sip_amount REAL,
        monthly_income REAL,
        emi_ratio REAL,
        bounce_count INTEGER,
        avg_balance REAL,
        credit_utilization REAL,
        job_stability_months INTEGER,
        monthly_expenses_ratio REAL,
        existing_loans_count INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        description TEXT,
        amount REAL,
        type TEXT,
        date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        phone TEXT,
        chat_history TEXT,
        loan_decision TEXT,
        date TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

# GENERATE FAKE DATA FOR NEW CUSTOMER
def generate_customer_data(phone, name, pan):
    account_number = "CRED" + str(random.randint(10000000, 99999999))
    account_type = random.choice(["Savings", "Current"])
    balance = round(random.uniform(5000, 500000), 2)
    branch = random.choice(["Mumbai Main", "Delhi Central", "Bangalore Tech Park", "Chennai Anna Nagar", "Hyderabad Hitech"])
    card_number = "**** **** **** " + str(random.randint(1000, 9999))
    card_type = random.choice(["Visa Debit", "Mastercard Debit", "Visa Credit", "Mastercard Credit"])
    cibil_score = random.randint(300, 900)
    outstanding_emi = random.randint(0, 50000)
    loan_amount = round(random.uniform(0, 1000000), 2)
    loan_status = random.choice(["ACTIVE", "CLOSED", "NONE"])
    loan_emi = round(loan_amount * 0.02, 2) if loan_status == "ACTIVE" else 0
    loan_tenure = random.randint(12, 60) if loan_status == "ACTIVE" else 0
    fd_amount = round(random.uniform(10000, 500000), 2)
    fd_maturity_date = (datetime.now() + timedelta(days=random.randint(180, 1825))).strftime("%Y-%m-%d")
    fd_interest_rate = round(random.uniform(5.0, 8.5), 2)
    fd_status = random.choice(["ACTIVE", "NONE"])
    mutual_fund_value = round(random.uniform(0, 200000), 2)
    sip_amount = round(random.uniform(500, 10000), 2)

    conn = sqlite3.connect("credify.db")
    c = conn.cursor()
    c.execute("""UPDATE users SET
        name=?, pan=?, customer_type="OLD",
        account_number=?, account_type=?, balance=?, branch=?,
        card_number=?, card_type=?, card_status="ACTIVE",
        cibil_score=?, outstanding_emi=?,
        loan_amount=?, loan_status=?, loan_emi=?, loan_tenure=?,
        fd_amount=?, fd_maturity_date=?, fd_interest_rate=?, fd_status=?,
        mutual_fund_value=?, sip_amount=?
        WHERE phone=?""",
        (name, pan, account_number, account_type, balance, branch,
         card_number, card_type, cibil_score, outstanding_emi,
         loan_amount, loan_status, loan_emi, loan_tenure,
         fd_amount, fd_maturity_date, fd_interest_rate, fd_status,
         mutual_fund_value, sip_amount, phone))

    # Generate fake transactions
    descriptions = [
        ("Amazon Purchase", "DEBIT"),
        ("Salary Credit", "CREDIT"),
        ("UPI Transfer", "DEBIT"),
        ("ATM Withdrawal", "DEBIT"),
        ("Interest Credit", "CREDIT"),
        ("Netflix Subscription", "DEBIT"),
        ("Swiggy Order", "DEBIT"),
        ("Refund Credit", "CREDIT"),
        ("EMI Debit", "DEBIT"),
        ("FD Interest", "CREDIT")
    ]
    for i in range(5):
        desc, txn_type = random.choice(descriptions)
        amount = round(random.uniform(100, 10000), 2)
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        c.execute("INSERT INTO transactions (phone, description, amount, type, date) VALUES (?, ?, ?, ?, ?)",
                  (phone, desc, amount, txn_type, date))

    conn.commit()
    conn.close()

    return {
        "account_number": account_number,
        "account_type": account_type,
        "balance": balance,
        "branch": branch,
        "card_number": card_number,
        "card_type": card_type,
        "cibil_score": cibil_score,
        "outstanding_emi": outstanding_emi,
        "loan_amount": loan_amount,
        "loan_status": loan_status,
        "loan_emi": loan_emi,
        "loan_tenure": loan_tenure,
        "fd_amount": fd_amount,
        "fd_maturity_date": fd_maturity_date,
        "fd_interest_rate": fd_interest_rate,
        "fd_status": fd_status,
        "mutual_fund_value": mutual_fund_value,
        "sip_amount": sip_amount
    }

# FETCH CUSTOMER DATA
def fetch_customer_data(phone):
    conn = sqlite3.connect("credify.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    c.execute("SELECT description, amount, type, date FROM transactions WHERE phone=? ORDER BY date DESC LIMIT 5", (phone,))
    transactions = c.fetchall()
    conn.close()

    if not row:
        return None

    return {
        "name": row[2],
        "pan": row[3],
        "account_number": row[5],
        "account_type": row[6],
        "balance": row[7],
        "branch": row[8],
        "card_number": row[9],
        "card_type": row[10],
        "card_status": row[11],
        "cibil_score": row[12],
        "outstanding_emi": row[13],
        "loan_amount": row[14],
        "loan_status": row[15],
        "loan_emi": row[16],
        "loan_tenure": row[17],
        "fd_amount": row[18],
        "fd_maturity_date": row[19],
        "fd_interest_rate": row[20],
        "fd_status": row[21],
        "mutual_fund_value": row[22],
        "sip_amount": row[23],
        "transactions": [{"description": t[0], "amount": t[1], "type": t[2], "date": t[3]} for t in transactions]
    }

# ML MODEL
weights = [-0.33984054423362736, 1.1717101389588829, 1.6879276286089038,
           -0.2960277263445141, 0.8747292330415741, -0.9385134269810018,
           0.4711343439806323, 0.7853401735488533]
bias = -1.0

def sigmoid(z):
    z = max(min(z, 500), -500)
    return 1 / (1 + math.exp(-z))

def predict(values):
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
    if prob >= 0.5:
        return "REJECTED", prob
    else:
        return "APPROVED", prob

# SYSTEM PROMPT
def get_system_prompt(customer_data):
    data_str = json.dumps(customer_data, indent=2)
    return f"""
You are Aria, a warm and friendly banking assistant for Credify Bank.
You have access to the customer's complete banking profile:

{data_str}

You can help with:
1. Account Information - balance, account number, account type, branch, mini statement
2. Cards - block/unblock card, replace card, change PIN, activate card
3. Payments - transfer money, UPI, NEFT, RTGS, IMPS (all simulated)
4. Statements - transaction history, download statement
5. Loans - check eligibility, apply for loan, EMI calculator, loan status
6. Deposits - open FD/RD, maturity calculator, close FD
7. Investments - mutual funds, SIPs, portfolio overview

For loan applications collect these 8 values naturally:
1. monthly_income
2. emi_ratio
3. bounce_count
4. avg_balance
5. credit_utilization
6. job_stability_months
7. monthly_expenses_ratio
8. existing_loans_count

Once you have ALL 8 loan values output EXACTLY:
COLLECTED:{{"monthly_income":50000,"emi_ratio":0.4,"bounce_count":2,"avg_balance":30000,"credit_utilization":60,"job_stability_months":24,"monthly_expenses_ratio":0.5,"existing_loans_count":1}}

For new customers who just registered, after displaying their profile ask:
PAN_COLLECTED:{{"pan": "ABCDE1234F", "name": "John"}}

RULES:
- Be warm, friendly and conversational
- Use the customer data to answer questions accurately
- For payments and transfers, simulate them naturally
- Never ask for information you already have
- Do NOT output COLLECTED until you have all 8 loan values
"""

# OTP ROUTES
@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    phone = data.get("phone")
    otp = str(random.randint(1000, 9999))

    conn = sqlite3.connect("credify.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (phone, otp) VALUES (?, ?)", (phone, otp))
    c.execute("UPDATE users SET otp=? WHERE phone=?", (otp, phone))
    conn.commit()
    conn.close()

    print(f"OTP for {phone}: {otp}")
    return jsonify({"success": True})

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    phone = data.get("phone")
    otp = data.get("otp")

    conn = sqlite3.connect("credify.db")
    c = conn.cursor()
    c.execute("SELECT otp, name FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == otp:
        if row[1] is not None:
            customer_data = fetch_customer_data(phone)
            # Refresh CIBIL
            new_cibil = random.randint(300, 900)
            new_emi = random.randint(0, 50000)
            conn = sqlite3.connect("credify.db")
            c = conn.cursor()
            c.execute("UPDATE users SET cibil_score=?, outstanding_emi=? WHERE phone=?",
                      (new_cibil, new_emi, phone))
            conn.commit()
            conn.close()
            customer_data["cibil_score"] = new_cibil
            customer_data["outstanding_emi"] = new_emi
            return jsonify({
                "success": True,
                "customer_type": "OLD",
                "customer_data": customer_data
            })
        else:
            return jsonify({
                "success": True,
                "customer_type": "NEW"
            })
    else:
        return jsonify({"success": False})

# REGISTER NEW CUSTOMER
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    phone = data.get("phone")
    name = data.get("name")
    pan = data.get("pan")

    customer_data = generate_customer_data(phone, name, pan)
    customer_data["name"] = name
    customer_data["pan"] = pan

    return jsonify({
        "success": True,
        "customer_data": customer_data
    })

# CHAT ROUTE
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    conversation_history = data.get("history", [])
    phone = data.get("phone", "")
    customer_data = data.get("customer_data", {})

    # Get last user message
    last_message = conversation_history[-1]["content"] if conversation_history else ""

    # The agent decides which tool to call
    try:
        reply = run_agent(customer_data, conversation_history, phone, last_message)
    except Exception as e:
        print("Agent error:", e)
        reply = "Sorry, something went wrong. Please try again."

    # Refresh account details after any action (balance, card status, FD)
    try:
        fresh = get_user_profile(phone)
        if isinstance(fresh, dict) and fresh:
            customer_data.update(fresh)
    except Exception:
        pass

    return jsonify({
        "reply": reply,
        "customer_data": customer_data
    })

# RUN
if __name__ == "__main__":
    app.run(debug=True, port=5000)