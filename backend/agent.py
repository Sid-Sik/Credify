from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from helper_agent import (
    get_account_details,
    get_balance,
    get_card_details,
    get_transactions,
    get_loan_details,
    get_fd_details,
    get_investment_details,
    get_cibil_details,
    get_user_profile
)
from worker_agent import (
    block_card,
    unblock_card,
    process_payment,
    open_fd,
    close_fd,
    process_loan_application,
    save_conversation
)
import json

# ── LLM ───────────────────────────────────────────────────────
llm = ChatGroq(
    api_key="YOUR_GROQ_API_KEY_HERE",
    model="llama-3.3-70b-versatile"
)

# ── TOOLS ─────────────────────────────────────────────────────
@tool
def tool_get_balance(phone: str) -> str:
    """Get the current account balance for a customer"""
    result = get_balance(phone)
    return json.dumps(result)

@tool
def tool_get_account_details(phone: str) -> str:
    """Get complete account details including account number, type and branch"""
    result = get_account_details(phone)
    return json.dumps(result)

@tool
def tool_get_transactions(phone: str) -> str:
    """Get last 5 transactions for a customer"""
    result = get_transactions(phone)
    return json.dumps(result)

@tool
def tool_get_card_details(phone: str) -> str:
    """Get card details including card number, type and status"""
    result = get_card_details(phone)
    return json.dumps(result)

@tool
def tool_block_card(phone: str) -> str:
    """Block the debit or credit card for a customer"""
    result = block_card(phone)
    return json.dumps(result)

@tool
def tool_unblock_card(phone: str) -> str:
    """Unblock the debit or credit card for a customer"""
    result = unblock_card(phone)
    return json.dumps(result)

@tool
def tool_get_loan_details(phone: str) -> str:
    """Get loan details including amount, EMI and status"""
    result = get_loan_details(phone)
    return json.dumps(result)

@tool
def tool_get_fd_details(phone: str) -> str:
    """Get fixed deposit details including amount, interest rate and maturity date"""
    result = get_fd_details(phone)
    return json.dumps(result)

@tool
def tool_open_fd(phone: str, amount: float, tenure_days: int) -> str:
    """Open a new fixed deposit for a customer"""
    result = open_fd(phone, amount, tenure_days)
    return json.dumps(result)

@tool
def tool_close_fd(phone: str) -> str:
    """Close an existing fixed deposit for a customer"""
    result = close_fd(phone)
    return json.dumps(result)

@tool
def tool_process_payment(phone: str, amount: float, recipient: str, method: str) -> str:
    """Process a payment transfer via UPI, NEFT, IMPS or RTGS"""
    result = process_payment(phone, amount, recipient, method)
    return json.dumps(result)

@tool
def tool_get_investment_details(phone: str) -> str:
    """Get investment details including mutual fund value and SIP amount"""
    result = get_investment_details(phone)
    return json.dumps(result)

@tool
def tool_get_cibil_details(phone: str) -> str:
    """Get CIBIL score and outstanding EMI details"""
    result = get_cibil_details(phone)
    return json.dumps(result)

@tool
def tool_process_loan(phone: str, monthly_income: float, emi_ratio: float,
                      bounce_count: int, avg_balance: float,
                      credit_utilization: float, job_stability_months: int,
                      monthly_expenses_ratio: float, existing_loans_count: int) -> str:
    """Process a loan application and get approval decision"""
    values = {
        "monthly_income": monthly_income,
        "emi_ratio": emi_ratio,
        "bounce_count": bounce_count,
        "avg_balance": avg_balance,
        "credit_utilization": credit_utilization,
        "job_stability_months": job_stability_months,
        "monthly_expenses_ratio": monthly_expenses_ratio,
        "existing_loans_count": existing_loans_count
    }
    result = process_loan_application(phone, values)
    return json.dumps(result)

# ── ALL TOOLS LIST ────────────────────────────────────────────
tools = [
    tool_get_balance,
    tool_get_account_details,
    tool_get_transactions,
    tool_get_card_details,
    tool_block_card,
    tool_unblock_card,
    tool_get_loan_details,
    tool_get_fd_details,
    tool_open_fd,
    tool_close_fd,
    tool_process_payment,
    tool_get_investment_details,
    tool_get_cibil_details,
    tool_process_loan
]

# ── CREATE AGENT ──────────────────────────────────────────────
def create_banking_agent(customer_data):
    name = customer_data.get("name", "Customer")
    balance = customer_data.get("balance", 0)
    cibil = customer_data.get("cibil_score", 0)
    card_status = customer_data.get("card_status", "ACTIVE")
    loan_status = customer_data.get("loan_status", "NONE")
    fd_status = customer_data.get("fd_status", "NONE")

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Aria, a warm and friendly personal banking assistant for Credify Bank.

You are talking to {name}.
Their current balance is Rs {balance:,.2f}
Their CIBIL score is {cibil}
Card status: {card_status}
Loan status: {loan_status}
FD status: {fd_status}

You have access to tools to help the customer.
Use tools to fetch real data and perform real actions.
Always be warm, personal and use the customer's name naturally.
Never make up data — always use tools to get real information.
After using a tool present the result in a friendly conversational way.
For loan applications collect all 8 values through natural conversation before calling the loan tool."""),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return executor

# ── RUN AGENT ─────────────────────────────────────────────────
def run_agent(customer_data, conversation_history, phone, user_message):
    executor = create_banking_agent(customer_data)

    # Convert history to LangChain format
    chat_history = []
    for msg in conversation_history[:-1]:
        if msg["role"] == "user":
            chat_history.append(("human", msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(("ai", msg["content"]))

    result = executor.invoke({
        "input": user_message,
        "chat_history": chat_history,
        "phone": phone
    })

    return result["output"]