import sqlite3
import json

DB_PATH = "credify.db"

# ── CONNECT TO DATABASE ───────────────────────────────────────
def get_connection():
    return sqlite3.connect(DB_PATH)

# ── GET COMPLETE USER PROFILE ─────────────────────────────────
def get_user_profile(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "phone": row[0],
        "otp": row[1],
        "name": row[2],
        "pan": row[3],
        "customer_type": row[4],
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
        "monthly_income": row[24],
        "emi_ratio": row[25],
        "bounce_count": row[26],
        "avg_balance": row[27],
        "credit_utilization": row[28],
        "job_stability_months": row[29],
        "monthly_expenses_ratio": row[30],
        "existing_loans_count": row[31]
    }

# ── GET BALANCE ───────────────────────────────────────────────
def get_balance(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    return {"balance": row[0]} if row else None

# ── GET CARD DETAILS ──────────────────────────────────────────
def get_card_details(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT card_number, card_type, card_status FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "card_number": row[0],
        "card_type": row[1],
        "card_status": row[2]
    }

# ── GET TRANSACTIONS ──────────────────────────────────────────
def get_transactions(phone, limit=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT description, amount, type, date FROM transactions WHERE phone=? ORDER BY date DESC LIMIT ?",
              (phone, limit))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "description": row[0],
            "amount": row[1],
            "type": row[2],
            "date": row[3]
        }
        for row in rows
    ]

# ── GET LOAN DETAILS ──────────────────────────────────────────
def get_loan_details(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT loan_amount, loan_status, loan_emi, loan_tenure FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "loan_amount": row[0],
        "loan_status": row[1],
        "loan_emi": row[2],
        "loan_tenure": row[3]
    }

# ── GET FD DETAILS ────────────────────────────────────────────
def get_fd_details(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT fd_amount, fd_maturity_date, fd_interest_rate, fd_status FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "fd_amount": row[0],
        "fd_maturity_date": row[1],
        "fd_interest_rate": row[2],
        "fd_status": row[3]
    }

# ── GET INVESTMENT DETAILS ────────────────────────────────────
def get_investment_details(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT mutual_fund_value, sip_amount FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "mutual_fund_value": row[0],
        "sip_amount": row[1]
    }

# ── GET CIBIL DETAILS ─────────────────────────────────────────
def get_cibil_details(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT cibil_score, outstanding_emi FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "cibil_score": row[0],
        "outstanding_emi": row[1]
    }

# ── GET ACCOUNT DETAILS ───────────────────────────────────────
def get_account_details(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT account_number, account_type, balance, branch FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "account_number": row[0],
        "account_type": row[1],
        "balance": row[2],
        "branch": row[3]
    }

# ── GET CONVERSATION HISTORY ──────────────────────────────────
def get_conversation_history(phone, limit=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT session_id, chat_history, loan_decision, timestamp FROM conversations WHERE phone=? ORDER BY timestamp DESC LIMIT ?",
              (phone, limit))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "session_id": row[0],
            "chat_history": json.loads(row[1]),
            "loan_decision": row[2],
            "timestamp": row[3]
        }
        for row in rows
    ]

# ── CHECK IF USER EXISTS ──────────────────────────────────────
def user_exists(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    return row is not None and row[0] is not None

# ── GET ML PARAMETERS ─────────────────────────────────────────
def get_ml_parameters(phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT monthly_income, emi_ratio, bounce_count, avg_balance,
              credit_utilization, job_stability_months, monthly_expenses_ratio,
              existing_loans_count FROM users WHERE phone=?""", (phone,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "monthly_income": row[0],
        "emi_ratio": row[1],
        "bounce_count": row[2],
        "avg_balance": row[3],
        "credit_utilization": row[4],
        "job_stability_months": row[5],
        "monthly_expenses_ratio": row[6],
        "existing_loans_count": row[7]
    }