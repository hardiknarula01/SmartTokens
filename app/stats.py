import time

_stats = {
    "total_requests": 0,
    "total_tokens_in": 0,
    "total_tokens_sent": 0,
    "total_tokens_saved": 0,
    "total_tokens_out": 0,
    "server_start_time": time.time()
}

def record(tokens_in: int, tokens_sent: int, tokens_out: int):
    _stats["total_requests"]     += 1
    _stats["total_tokens_in"]    += tokens_in
    _stats["total_tokens_sent"]  += tokens_sent
    _stats["total_tokens_saved"] += (tokens_in - tokens_sent)
    _stats["total_tokens_out"]   += tokens_out

def get_stats() -> dict:
    saved    = _stats["total_tokens_saved"]
    total_in = _stats["total_tokens_in"]
    avg      = round((saved / total_in * 100), 1) if total_in > 0 else 0
    uptime   = round(time.time() - _stats["server_start_time"])
    return {
        "total_requests":     _stats["total_requests"],
        "total_tokens_in":    _stats["total_tokens_in"],
        "total_tokens_sent":  _stats["total_tokens_sent"],
        "total_tokens_saved": _stats["total_tokens_saved"],
        "total_tokens_out":   _stats["total_tokens_out"],
        "avg_reduction_pct":  f"{avg}%",
        "uptime_seconds":     uptime
    }