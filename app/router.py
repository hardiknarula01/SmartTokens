import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.counter import count_tokens
from app.preprocessor import preprocess
from app.db import log_event
from app.stats import record

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

router = APIRouter()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_headers():
    key = os.getenv('GROQ_API_KEY', '')
    if not key:
        raise ValueError("GROQ_API_KEY is not set. Check your .env file.")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

@router.post("/messages")
async def messages(request: Request):
    body = await request.json()

    # Step 1: Count original tokens
    original_text = " ".join(
        m.get("content", "") if isinstance(m.get("content"), str) else ""
        for m in body.get("messages", [])
    )
    tokens_in = count_tokens(original_text)

    # Step 2: Preprocess each message
    for msg in body.get("messages", []):
        if isinstance(msg.get("content"), str):
            try:
                msg["content"] = preprocess(msg["content"])
            except Exception as e:
                print(f"Preprocessor skipped: {e}")

    # Step 3: Count tokens after preprocessing
    processed_text = " ".join(
        m.get("content", "") if isinstance(m.get("content"), str) else ""
        for m in body.get("messages", [])
    )
    tokens_sent = count_tokens(processed_text)

    # Step 4: Send to Groq
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                GROQ_URL,
                json=body,
                headers=get_headers()
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="SmartToken: Groq timed out")

    result = response.json()

    # Step 5: Count output tokens
    output_text = ""
    try:
        output_text = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        pass
    tokens_out = count_tokens(output_text)

    # Step 6: Record in memory stats
    record(tokens_in, tokens_sent, tokens_out)

    # Step 7: Log to database
    await log_event(
        tokens_in=tokens_in,
        tokens_sent=tokens_sent,
        tokens_out=tokens_out,
        model=body.get("model", "unknown")
    )

    # Step 8: Calculate savings
    tokens_saved  = tokens_in - tokens_sent
    reduction_pct = round((tokens_saved / tokens_in * 100), 1) if tokens_in > 0 else 0

    # Step 9: Return wrapped response
    return JSONResponse(
        content={
            "smarttoken": {
                "tokens_in":     tokens_in,
                "tokens_sent":   tokens_sent,
                "tokens_saved":  tokens_saved,
                "tokens_out":    tokens_out,
                "reduction_pct": f"{reduction_pct}%",
                "model_used":    body.get("model", "unknown")
            },
            "result": result
        },
        headers={
            "X-SmartToken-Tokens-In":    str(tokens_in),
            "X-SmartToken-Tokens-Sent":  str(tokens_sent),
            "X-SmartToken-Tokens-Saved": str(tokens_saved),
            "X-SmartToken-Reduction":    f"{reduction_pct}%"
        }
    )