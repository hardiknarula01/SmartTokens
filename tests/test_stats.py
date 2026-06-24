from app.stats import record, get_stats, _stats
import time

def setup_function():
    _stats["total_requests"]     = 0
    _stats["total_tokens_in"]    = 0
    _stats["total_tokens_sent"]  = 0
    _stats["total_tokens_saved"] = 0
    _stats["total_tokens_out"]   = 0
    _stats["server_start_time"]  = time.time()

def test_record_increases_request_count():
    record(100, 80, 50)
    assert _stats["total_requests"] == 1

def test_record_calculates_tokens_saved():
    record(100, 80, 50)
    assert _stats["total_tokens_saved"] == 20

def test_get_stats_returns_correct_reduction():
    record(100, 80, 50)
    result = get_stats()
    assert result["avg_reduction_pct"] == "20.0%"

def test_multiple_records_accumulate():
    record(100, 80, 50)
    record(200, 140, 80)
    assert _stats["total_requests"]     == 2
    assert _stats["total_tokens_in"]    == 300
    assert _stats["total_tokens_saved"] == 80

def test_stats_uptime_is_positive():
    result = get_stats()
    assert result["uptime_seconds"] >= 0