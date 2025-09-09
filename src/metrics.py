from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps

# Define metrics
tool_calls_total = Counter(
    'mcp_tool_calls_total',
    'Total number of tool calls',
    ['tool', 'status']
)

tool_duration_seconds = Histogram(
    'mcp_tool_duration_seconds',
    'Duration of tool execution in seconds',
    ['tool']
)

active_connections = Gauge(
    'mcp_active_connections',
    'Number of active MCP connections'
)

def track_metrics(tool_name: str):
    """Decorator to track tool metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                tool_calls_total.labels(tool=tool_name, status='success').inc()
                return result
            except Exception as e:
                tool_calls_total.labels(tool=tool_name, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                tool_duration_seconds.labels(tool=tool_name).observe(duration)
        return wrapper
    return decorator