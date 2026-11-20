Credify

A banking chatbot I built during my data analytics internship at EY, from May to July 2026.

I wanted to see if a language model could handle everyday banking tasks without me writing a rule for every sentence a customer might say. You chat with an assistant called Aria. She can check your balance, block a card, send money, open a fixed deposit or take a loan application. I built every part myself: the chat page, the backend, the database, the loan model and the agent.

What Aria can do

- Tell you your balance, account details, recent transactions and CIBIL score

- Block or unblock your card

- Send money by UPI, NEFT, IMPS or RTGS

- Show, open or close a fixed deposit

- Show your mutual fund and SIP details

- Take a loan application by chatting. She asks a few things in normal conversation and then a model decides.

How it works

The chat page is plain HTML, CSS and JavaScript. It talks to a Flask backend, and everything is saved in SQLite. Aria runs on Llama 3.3 70B through Groq.

The main part is agent.py. I used LangChain and gave the model 14 tools, one for each banking action, each with a short description. The model reads the descriptions and decides which tool fits what the customer said. My first version used if/else code and keyword matching, and it broke whenever someone phrased something differently. That older router is still in orchestrator_agent.py if you want to compare.

The loan model

I wrote the logistic regression by hand in plain Python, with no scikit-learn, because I wanted to understand what the library does underneath. It looks at 8 things: income, EMI ratio, bounced payments, average balance, credit utilisation, months in the current job, expense ratio and number of existing loans.

At one point the weights kept blowing up during training. The fix was dividing the gradient by the number of samples.

It trained on 500 records that I generated myself and reaches 80.6 percent training accuracy (precision 0.71, recall 0.55, F1 0.62). Since the data is made up, these numbers describe how the model behaves on that data. They say nothing about real customers.

What is where

- backend: the Flask app, the agent and the database functions

- frontend: the chat page

- ml: the model code and the dataset

Running it

First install the packages with this command:

pip install flask flask-cors groq "langchain>=0.3,<1.0" "langchain-groq>=0.3,<1.0"

Then get a free key from console.groq.com and set it:

export GROQ_API_KEY="your_key"

Start the backend:

cd backend && python3 app.py

Open frontend/index.html with a local server, such as VS Code Live Server, and enter any phone number. The OTP appears in the terminal where the backend is running. The database creates itself the first time you run it.

Good to know

All the customer data is generated. The OTP prints in the terminal instead of arriving by SMS, and payments only change the local database. It runs on my laptop and is not deployed anywhere. A real bank would need real integrations, much stronger security and regulatory compliance.
