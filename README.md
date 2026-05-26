# model-router-budget

A FastAPI backend with a simple dashboard UI for routing prompts by difficulty, checking budget before any LLM call, logging requests to SQLite, and supporting fake, DeepSeek, and OpenAI providers.

This demo uses one global monthly budget for the whole app.

## Run the backend

```bash
cd /Users/revanthbarik/model-router-budget
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The backend runs at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Run the UI

The UI is served by FastAPI, so you do not need a separate frontend server.

Open:

- [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui)
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Environment (`.env`)

```env
LLM_PROVIDER=fake
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
MONTHLY_BUDGET=1.00
MAX_PROMPT_CHARS=4000
```

## Modes

- Fake mode is the default and does not spend money.
- DeepSeek mode is used when `LLM_PROVIDER=deepseek`.
- OpenAI mode is used when `LLM_PROVIDER=openai`.
- If a provider key is missing or the provider call fails, the app falls back safely to fake mode instead of crashing.
- `USE_REAL_LLM=true` is still supported for backwards compatibility and maps to DeepSeek if `LLM_PROVIDER` is not set.

## Monthly budget behavior

- Budget is calculated from `billable_cost` for logs in the current calendar month only.
- Server restart does not reset the budget.
- A new month naturally starts a fresh budget window.
- Old logs stay in the database and still appear in prompt history.
- Fake, fallback, and blocked requests do not reduce budget.
- In a production version, this would usually become a per-user or per-workspace budget system.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ui` | Dashboard UI |
| GET | `/health` | Health check |
| POST | `/route` | Route a prompt |
| GET | `/budget` | Budget status |
| GET | `/logs` | Recent request logs |
| GET | `/metrics` | Usage metrics |

## Test fake mode

1. Put this in `.env`:

```env
LLM_PROVIDER=fake
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
MONTHLY_BUDGET=1.00
MAX_PROMPT_CHARS=4000
```

2. Start the backend.
3. Open `/ui`.
4. Submit a prompt.
5. Confirm the result shows the `Fake` mode badge.

## Test real DeepSeek mode

1. Put this in `.env`:

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_real_key_here
OPENAI_API_KEY=
MONTHLY_BUDGET=1.00
MAX_PROMPT_CHARS=4000
```

2. Restart the backend.
3. Submit a prompt from `/ui`.
4. If DeepSeek works, the mode badge should show `DeepSeek Live`.
5. If DeepSeek fails, the app should still return a fake fallback response without crashing.

## Test OpenAI mode

1. Put this in `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_real_key_here
DEEPSEEK_API_KEY=
MONTHLY_BUDGET=1.00
MAX_PROMPT_CHARS=4000
```

2. Restart the backend.
3. Submit a prompt from `/ui`.
4. If OpenAI works, the mode badge should show `OpenAI Live`.
5. If OpenAI fails, the app should still return a fake fallback response without crashing.

## Test budget blocking

1. Put this in `.env`:

```env
MONTHLY_BUDGET=0.0001
LLM_PROVIDER=fake
```

2. Restart the backend.
3. Submit a longer prompt.
4. The request should show `blocked`.
5. The dashboard should display the red warning message.
6. The request should appear in logs and prompt history as blocked, and no provider call should be made.

## Prompt history

- The dashboard now includes a `Prompt History` section.
- It uses expandable history items for recent prompts.
- Each item shows the saved prompt, answer, provider, LLM mode, model, tier, difficulty, cost, latency, budget status, and timestamp.

## Common issues

- `Address already in use`: stop the old server process on port 8000 and rerun Uvicorn.
- `ModuleNotFoundError`: make sure the virtual environment is activated and dependencies are installed.
- `DeepSeek not working`: check `USE_REAL_LLM=true`, confirm the API key is set, then restart the backend.
- `Prompt is too long`: either shorten the prompt or raise `MAX_PROMPT_CHARS` in `.env`.
- `Budget exceeded`: raise `MONTHLY_BUDGET` in `.env` or lower the prompt size.
