# SmartTokens 🛡️

> AI Token Optimization Proxy — Reduce your AI API costs by 50–80% with zero code changes.

SmartToken sits between your application and any AI model API. It cleans, compresses, and optimizes every prompt before sending — so you pay for less tokens without losing any response quality.

---

## What it does
Your App  →  SmartToken  →  Groq / OpenAI / Gemini / Claude

↓

Cleans HTML tags

Removes extra spaces

Strips blank lines

Counts tokens saved

Logs to PostgreSQL

## Results

| Prompt Type        | Tokens Before | Tokens After | Saving |
|--------------------|---------------|--------------|--------|
| Clean plain text   | 7             | 7            | 0%     |
| HTML from website  | 45            | 18           | 60%    |
| Copy-pasted doc    | 94            | 33           | 64.9%  |
| Real enterprise data | 200+        | 60–80        | 65–75% |

---

## Tech Stack

| Layer        | Technology          | Purpose                        |
|--------------|---------------------|--------------------------------|
| API Server   | FastAPI + uvicorn   | Receives and returns requests  |
| Optimization | Python regex + ftfy | Cleans and compresses prompts  |
| Token Count  | tiktoken            | Counts tokens before and after |
| Database     | PostgreSQL          | Stores savings history forever |
| Container    | Docker              | Runs PostgreSQL locally        |
| AI Provider  | Groq (Llama 3.3)    | Free fast AI model             |

---

## Project Structure
 
 ![Architecture](docs/flow.svg)

 SmartTokens/

├── app/

│   ├── init.py          # Makes app a Python package

│   ├── main.py              # FastAPI app entry point

│   ├── router.py            # /v1/messages endpoint

│   ├── counter.py           # Token counting with tiktoken

│   ├── preprocessor.py      # Text cleaning pipeline

│   ├── db.py                # PostgreSQL connection and queries

│   └── stats.py             # In-memory stats tracker

├── tests/

│   ├── init.py

│   ├── test_preprocessor.py # Tests for text cleaning

│   ├── test_stats.py        # Tests for stats tracking

│   └── test_db.py           # Tests for database layer

├── .env                     # API keys — never commit this

├── .gitignore               # Ignores secrets and venv

├── docker-compose.yml       # Runs PostgreSQL in Docker

├── requirements.txt         # Python dependencies

└── README.md                # This file

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker Desktop
- A free Groq API key from https://console.groq.com

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/SmartTokens.git
cd SmartTokens
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/Scripts/activate   # Windows
source venv/bin/activate       # Mac / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables


Create a `.env` file in the root folder:
GROQ_API_KEY=your_groq_key_here

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smarttoken
Get your free Groq key at https://console.groq.com

### 5. Start PostgreSQL with Docker

```bash
docker-compose up -d
```

### 6. Run tests

```bash
pytest tests/ -v
```

All 12 tests should pass.

### 7. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:

✅ Database connected and table ready.

INFO:     Uvicorn running on http://127.0.0.1:8000

---

## API Reference

### Health Check
GET /health

Response:
```json
{
  "status": "ok",
  "version": "0.3.0"
}
```

---

### Send a Message
POST /v1/messages

Request body:
```json
{
  "model": "llama-3.3-70b-versatile",
  "max_tokens": 100,
  "messages": [
    {
      "role": "user",
      "content": "Your prompt here"
    }
  ]
}
```

Response:
```json
{
  "smarttoken": {
    "tokens_in": 94,
    "tokens_sent": 33,
    "tokens_saved": 61,
    "tokens_out": 21,
    "reduction_pct": "64.9%",
    "model_used": "llama-3.3-70b-versatile"
  },
  "result": {
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "AI response here"
        }
      }
    ]
  }
}
```

Response headers:
X-SmartToken-Tokens-In:    94

X-SmartToken-Tokens-Sent:  33

X-SmartToken-Tokens-Saved: 61

X-SmartToken-Reduction:    64.9%

---

### View Stats
GET /stats
Response:
```json
{
  "source": "database",
  "total_requests": 10,
  "total_tokens_in": 940,
  "total_tokens_sent": 330,
  "total_tokens_saved": 610,
  "total_tokens_out": 420,
  "avg_reduction_pct": "64.9%"
}
```

---

## What SmartToken removes

| Noise Type       | Example                          | Token Saving |
|------------------|----------------------------------|--------------|
| HTML tags        | `<div><p><b>text</b></p></div>`  | 10–30%       |
| Extra spaces     | `what   is   python`             | 5–15%        |
| Blank lines      | `\n\n\n\n\n`                     | 5–20%        |
| Separator lines  | `========` `--------`            | 2–10%        |
| All combined     | Real copy-paste enterprise data  | 40–70%       |

---

## Supported AI Models

SmartToken works with any OpenAI-compatible API.

| Provider  | Model                    | Cost      |
|-----------|--------------------------|-----------|
| Groq      | llama-3.3-70b-versatile  | Free      |
| Groq      | llama-3.1-8b-instant     | Free      |
| Gemini    | gemini-2.0-flash         | Free      |
| OpenAI    | gpt-4o-mini              | Paid      |
| OpenAI    | gpt-4o                   | Paid      |
| Anthropic | claude-haiku-4-5         | Paid      |
| Anthropic | claude-sonnet-4-6        | Paid      |

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_preprocessor.py -v

# Run with coverage report
pytest tests/ -v --cov=app
```

---

## Environment Variables

| Variable       | Required | Description                              |
|----------------|----------|------------------------------------------|
| GROQ_API_KEY   | Yes      | Your Groq API key from console.groq.com  |
| DATABASE_URL   | Yes      | PostgreSQL connection string             |
| OPENAI_API_KEY | No       | Only needed if using OpenAI models       |
| GEMINI_API_KEY | No       | Only needed if using Gemini models       |

---

## License

This project is licensed under the Apache License 2.0.

Copyright © 2026 Hardik Narula

You may use, modify, and distribute this software in accordance with the terms of the Apache License 2.0. See the LICENSE file for details.
---

## Author

Built by Hardik Narula

---

*SmartToken — Every token counts.*
