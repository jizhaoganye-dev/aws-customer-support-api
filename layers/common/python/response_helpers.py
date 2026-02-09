"""
Shared Lambda response helpers.
Standard JSON response formatting with CORS headers.
"""
import json
from typing import Any, Optional


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def success_response(body: Any, status_code: int = 200) -> dict:
    """Return a successful API Gateway proxy response."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def error_response(message: str, status_code: int = 400, details: Optional[dict] = None) -> dict:
    """Return an error API Gateway proxy response."""
    body = {"error": message}
    if details:
        body["details"] = details
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


def parse_body(event: dict) -> Optional[dict]:
    """Parse JSON body from API Gateway event, returning None on failure."""
    body = event.get("body")
    if body is None:
        return None
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return body
