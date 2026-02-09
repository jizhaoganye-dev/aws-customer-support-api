"""
Health Check Lambda Function.
GET /api/health

Returns system health status including:
- Database connectivity
- AI API availability
- Lambda memory/runtime info
"""
import os
import logging
from datetime import datetime

from response_helpers import success_response, error_response
from db import check_health as check_db_health

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _check_ai_api() -> dict:
    """Check if Claude Opus 4.6 API is configured and reachable."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"status": "unconfigured", "provider": "anthropic"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Minimal API call to verify connectivity
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=5,
            messages=[{"role": "user", "content": "ping"}],
        )
        return {"status": "healthy", "provider": "anthropic", "model": "claude-sonnet-4-20250514"}
    except Exception as e:
        return {"status": "unhealthy", "provider": "anthropic", "error": str(e)}


def lambda_handler(event, context):
    """
    Health check endpoint.
    Returns connectivity status for all downstream services.
    """
    logger.info("Health check invoked")

    # Database health
    db_health = check_db_health()

    # AI API health
    ai_health = _check_ai_api()

    # Lambda runtime info
    runtime_info = {
        "function_name": context.function_name if context else "local",
        "memory_limit_mb": context.memory_limit_in_mb if context else "N/A",
        "remaining_time_ms": context.get_remaining_time_in_millis() if context else "N/A",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "region": os.environ.get("AWS_REGION", "unknown"),
    }

    overall_status = "healthy"
    if db_health["status"] != "healthy":
        overall_status = "degraded"
    if ai_health["status"] == "unhealthy":
        overall_status = "degraded"

    return success_response({
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_health,
            "ai_api": ai_health,
        },
        "runtime": runtime_info,
    })
