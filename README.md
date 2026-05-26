# Model Router with Budgets

A FastAPI-based AI backend that routes user prompts to different LLM providers based on prompt difficulty, estimated cost, and available monthly budget.

The project supports fake mode, DeepSeek, and OpenAI providers. It also includes a simple dashboard UI for submitting prompts, viewing routing decisions, checking budget usage, and inspecting request history.

---

## Why I Built This

LLM applications often send every request to the same powerful model, even when a cheaper model would be enough. This can increase API costs quickly, especially when users send many prompts.

I built this project to understand how AI systems can make routing decisions before calling an LLM. The goal was to build a small backend system that thinks about:

- How difficult the prompt is
- Which model tier is suitable
- Whether the request fits within the available budget
- How much the request may cost
- How to log usage, latency, and provider behavior

---

## The Problem

Most basic AI apps directly call an LLM after receiving a prompt.

This project adds a decision layer before the LLM call.

Instead of blindly sending every request to a model, the system:

1. Receives the user prompt
2. Estimates the prompt difficulty
3. Selects a suitable model/provider
4. Checks the remaining monthly budget
5. Calls the selected provider only if budget allows
6. Logs the request, cost, latency, and response details

This makes the project useful for understanding cost-aware AI backend design.

---

## Features

- Prompt difficulty estimation
- Budget-aware request blocking
- Support for fake, DeepSeek, and OpenAI providers
- SQLite logging for prompt history
- Monthly budget tracking
- Latency and cost tracking
- Fallback to fake mode if a real provider fails
- FastAPI backend
- Built-in dashboard UI served by FastAPI
- Swagger docs for API testing

---

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- Uvicorn
- DeepSeek API
- OpenAI API
- HTML/CSS/JavaScript dashboard

---

## How It Works

```text
User Prompt
    ↓
FastAPI Backend
    ↓
Prompt Difficulty Estimator
    ↓
Model / Provider Selection
    ↓
Budget Check
    ↓
LLM Provider Call
    ↓
Cost + Latency Logging
    ↓
Dashboard / API Response


#Budget Behavior:
This demo uses one global monthly budget for the whole app.
Budget is calculated from billable_cost for logs in the current calendar month only.
Server restart does not reset the budget.
A new month naturally starts a fresh budget window.
Old logs stay in the database and still appear in prompt history.
Fake, fallback, and blocked requests do not reduce budget.
In a production version, this would usually become a per-user or per-workspace budget system.

#How To Run The Project

1.Clone the repository:
git clone https://github.com/YOUR_USERNAME/model-router-budget.git
cd model-router-budget

2.Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate
For Windows:
.venv\Scripts\activate

3.Install dependencies:
pip install -r requirements.txt
Create your environment file:
cp .env.example .env

4.Run the backend:
uvicorn app.main:app --reload
The backend runs at:
http://127.0.0.1:8000

What I Learned
While building this project, I learned:
How to structure a FastAPI backend
How to design an LLM routing layer
How to estimate prompt difficulty before calling a model
How to track cost, latency, and provider behavior
How to use SQLite for request logging
How budget checks can be added before expensive API calls
How fallback behavior improves reliability in AI applications

Future Improvements
Add user-based budgets instead of one global budget
Add authentication
Improve prompt difficulty estimation
Add more model providers
Add better analytics and charts
Deploy the backend and dashboard
Add Docker support