// GLOBAL VARIABLES
let conversationHistory = [];
let userPhone = "";
let customerType = "NEW";
let customerData = {};

// SCREEN SWITCHER
function showScreen(screenId) {
    document.getElementById("otpScreen").style.display = "none";
    document.getElementById("chatScreen").style.display = "none";
    document.getElementById(screenId).style.display = "flex";
}

// OTP SCREEN LOGIC
document.getElementById("sendOtpBtn").addEventListener("click", function () {
    const phone = document.getElementById("phoneInput").value.trim();
    if (phone.length !== 10) {
        alert("Please enter a valid 10 digit phone number!");
        return;
    }
    userPhone = phone;

    fetch("http://127.0.0.1:5000/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: phone })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("otpSection").style.display = "block";
        document.getElementById("otpMessage").textContent = "OTP sent! Check terminal for OTP.";
    });
});

document.getElementById("verifyOtpBtn").addEventListener("click", function () {
    const otp = document.getElementById("otpInput").value.trim();

    fetch("http://127.0.0.1:5000/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: userPhone, otp: otp })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            customerType = data.customer_type;
            if (data.customer_type === "OLD") {
                customerData = data.customer_data;
            }
            showScreen("chatScreen");
            startChat();
        } else {
            document.getElementById("otpMessage").textContent = "Invalid OTP. Please try again!";
            document.getElementById("otpMessage").style.color = "#ef4444";
        }
    });
});

// CHAT SCREEN LOGIC
function startChat() {
    let welcomeMessage = "";

    if (customerType === "OLD") {
        const d = customerData;
        welcomeMessage = `Welcome back ${d.name}! 😊

Here is your account summary:

Account Number: ${d.account_number}
Account Type: ${d.account_type}
Balance: Rs ${d.balance.toLocaleString()}
Branch: ${d.branch}

Card: ${d.card_number} (${d.card_type}) - ${d.card_status}

CIBIL Score: ${d.cibil_score}
Outstanding EMI: Rs ${d.outstanding_emi.toLocaleString()}

Loan Status: ${d.loan_status}${d.loan_status === "ACTIVE" ? `\nLoan EMI: Rs ${d.loan_emi.toLocaleString()} for ${d.loan_tenure} months` : ""}

FD Status: ${d.fd_status}${d.fd_status === "ACTIVE" ? `\nFD Amount: Rs ${d.fd_amount.toLocaleString()} @ ${d.fd_interest_rate}% maturing on ${d.fd_maturity_date}` : ""}

Mutual Fund Value: Rs ${d.mutual_fund_value.toLocaleString()}
SIP Amount: Rs ${d.sip_amount.toLocaleString()} per month

How can I help you today?`;

    } else {
        welcomeMessage = `Hi there! 👋 Welcome to Credify. I'm Aria, your personal banking assistant. Could you please tell me your name?`;
    }

    displayAriaMessage(welcomeMessage);
    conversationHistory.push({
        role: "assistant",
        content: welcomeMessage
    });
}

function displayAriaMessage(message) {
    const chatWindow = document.getElementById("chatWindow");
    const bubble = document.createElement("div");
    bubble.classList.add("aria-bubble");
    bubble.textContent = message;
    chatWindow.appendChild(bubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function displayUserMessage(message) {
    const chatWindow = document.getElementById("chatWindow");
    const bubble = document.createElement("div");
    bubble.classList.add("user-bubble");
    bubble.textContent = message;
    chatWindow.appendChild(bubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

document.getElementById("sendBtn").addEventListener("click", function () {
    handleUserInput();
});

document.getElementById("userInput").addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        handleUserInput();
    }
});

function handleUserInput() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (message === "") return;

    displayUserMessage(message);
    conversationHistory.push({ role: "user", content: message });
    input.value = "";
    callBackend();
}

// CALL BACKEND
async function callBackend() {
    const lastUserMsg = conversationHistory[conversationHistory.length - 1].content;

    // Check if new customer giving PAN
    if (customerType === "NEW" && !customerData.account_number) {
        const panMatch = lastUserMsg.match(/[A-Z]{5}[0-9]{4}[A-Z]{1}/);
        if (panMatch) {
            const regResponse = await fetch("http://127.0.0.1:5000/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone: userPhone,
                    name: customerData.name || "Customer",
                    pan: panMatch[0]
                })
            });
            const regData = await regResponse.json();
            customerData = regData.customer_data;
            customerType = "OLD";

            const d = customerData;
            const summaryMessage = `Thank you! Here is your banking profile:

Account Number: ${d.account_number}
Account Type: ${d.account_type}
Balance: Rs ${d.balance.toLocaleString()}
Branch: ${d.branch}
Card: ${d.card_number} (${d.card_type})
CIBIL Score: ${d.cibil_score}
Outstanding EMI: Rs ${d.outstanding_emi.toLocaleString()}
Loan Status: ${d.loan_status}
FD Status: ${d.fd_status}
Mutual Fund Value: Rs ${d.mutual_fund_value.toLocaleString()}
SIP: Rs ${d.sip_amount.toLocaleString()} per month

How can I help you today?`;

            conversationHistory.push({ role: "assistant", content: summaryMessage });
            displayAriaMessage(summaryMessage);
            return;
        }
    }

    // Normal chat
    const response = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            history: conversationHistory,
            phone: userPhone,
            customer_data: customerData
        })
    });

  const data = await response.json();

if (data.customer_data) {
    customerData = data.customer_data;
}

if (data.reply) {
    conversationHistory.push({ role: "assistant", content: data.reply });
    displayAriaMessage(data.reply);
}

if (data.session_id) {
    displayAriaMessage(`Your session ID is ${data.session_id}. Please save this for reference.`);
}
}
