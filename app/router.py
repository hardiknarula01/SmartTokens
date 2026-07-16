import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.counter import count_tokens
from app.preprocessor import preprocess
from app.compressor import compress
from app.db import log_event
from app.stats import record
from app.cache import get_cached, set_cached

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

def extract_prompt(body: dict) -> str:
    """Extract the full prompt text from the request body."""
    return " ".join(
        m.get("content", "") if isinstance(m.get("content"), str) else ""
        for m in body.get("messages", [])
    )

@router.post("/messages")
async def messages(request: Request):
    body  = await request.json()
    model = body.get("model", "unknown")

    # ── Step 0: Check cache FIRST before doing anything ──────────────────────
    # Concept: early return
    # If we find a cached result we return immediately.
    # No preprocessing, no compression, no Groq call.
    # This is the fastest possible response — just a Redis lookup.
    original_prompt = extract_prompt(body)
    cached_result   = await get_cached(original_prompt, model)

    if cached_result:
        # Cache hit — return immediately with zero token cost
        tokens_in = count_tokens(original_prompt)
        return JSONResponse(
            content={
                "smarttoken": {
                    "tokens_in":              tokens_in,
                    "tokens_after_preprocess": tokens_in,
                    "tokens_sent":            0,      # zero tokens sent to Groq
                    "tokens_out":             0,
                    "savings_breakdown": {
                        "preprocess_saved": 0,
                        "compress_saved":   0,
                        "total_saved":      tokens_in,  # all tokens saved
                        "cache_hit":        True        # flag showing cache was used
                    },
                    "reduction_pct":  "100.0%",         # 100% savings on cache hit
                    "model_used":     model,
                    "cache_hit":      True
                },
                "result": cached_result
            },
            headers={
                "X-SmartToken-Cache":        "HIT",
                "X-SmartToken-Tokens-In":    str(tokens_in),
                "X-SmartToken-Tokens-Sent":  "0",
                "X-SmartToken-Tokens-Saved": str(tokens_in),
                "X-SmartToken-Reduction":    "100.0%"
            }
        )

    # ── Step 1: Count original tokens ─────────────────────────────────────────
    tokens_in = count_tokens(original_prompt)

    # ── Step 2: Preprocess ────────────────────────────────────────────────────
    for msg in body.get("messages", []):
        if isinstance(msg.get("content"), str):
            try:
                msg["content"] = preprocess(msg["content"])
            except Exception as e:
                print(f"Preprocessor skipped: {e}")

    tokens_after_preprocess = count_tokens(extract_prompt(body))

    # ── Step 3: Compress ──────────────────────────────────────────────────────
    for msg in body.get("messages", []):
        if isinstance(msg.get("content"), str):
            try:
                msg["content"] = compress(msg["content"])
            except Exception as e:
                print(f"Compressor skipped: {e}")

    tokens_sent = count_tokens(extract_prompt(body))

    # ── Step 4: Send to Groq ──────────────────────────────────────────────────
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

    # ── Step 5: Store result in cache for next time ───────────────────────────
    # Concept: store using ORIGINAL prompt as key not compressed prompt
    # This way future requests with the same original prompt get a cache hit
    await set_cached(original_prompt, model, result)

    # ── Step 6: Count output tokens ───────────────────────────────────────────
    output_text = ""
    try:
        output_text = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        pass
    tokens_out = count_tokens(output_text)

    # ── Step 7: Record stats ──────────────────────────────────────────────────
    record(tokens_in, tokens_sent, tokens_out)
    await log_event(
        tokens_in=tokens_in,
        tokens_sent=tokens_sent,
        tokens_out=tokens_out,
        model=model
    )

    # ── Step 8: Return response ───────────────────────────────────────────────
    preprocess_saved = tokens_in - tokens_after_preprocess
    compress_saved   = tokens_after_preprocess - tokens_sent
    total_saved      = tokens_in - tokens_sent
    reduction_pct    = round((total_saved / tokens_in * 100), 1) if tokens_in > 0 else 0

    return JSONResponse(
        content={
            "smarttoken": {
                "tokens_in":               tokens_in,
                "tokens_after_preprocess": tokens_after_preprocess,
                "tokens_sent":             tokens_sent,
                "tokens_out":              tokens_out,
                "savings_breakdown": {
                    "preprocess_saved": preprocess_saved,
                    "compress_saved":   compress_saved,
                    "total_saved":      total_saved,
                    "cache_hit":        False
                },
                "reduction_pct": f"{reduction_pct}%",
                "model_used":    model,
                "cache_hit":     False
            },
            "result": result
        },
        headers={
            "X-SmartToken-Cache":        "MISS",
            "X-SmartToken-Tokens-In":    str(tokens_in),
            "X-SmartToken-Tokens-Sent":  str(tokens_sent),
            "X-SmartToken-Tokens-Saved": str(total_saved),
            "X-SmartToken-Reduction":    f"{reduction_pct}%"
        }
    )