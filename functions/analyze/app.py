"""
Analyze Lambda Function — Harassment Detection + Sentiment Analysis API.
POST /api/analyze

Accepts: { "message": "...", "conversation_id": "..." }
Returns: { "harassment": {...}, "sentiment": {...}, "combined_risk": "..." }

Provides a dedicated analysis endpoint for real-time dashboard monitoring.
"""
import json
import os
import logging
from datetime import datetime

from response_helpers import success_response, error_response, parse_body
from harassment_detector import detect_harassment, Severity
from sentiment_analyzer import analyze_sentiment, Sentiment
from db import execute_insert

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _calculate_combined_risk(harassment_severity: str, sentiment: str) -> str:
    """
    Calculate combined risk level from harassment severity and sentiment.

    Risk Matrix:
        harassment\sentiment | anger | negative | neutral | positive
        critical             |  🔴   |    🔴    |   🔴    |    🟠
        high                 |  🔴   |    🟠    |   🟠    |    🟡
        medium               |  🟠   |    🟡    |   🟡    |    🟢
        low                  |  🟡   |    🟡    |   🟢    |    🟢
        none                 |  🟡   |    🟢    |   🟢    |    🟢
    """
    risk_matrix = {
        ("critical", "anger"): "critical",
        ("critical", "negative"): "critical",
        ("critical", "neutral"): "critical",
        ("critical", "positive"): "high",
        ("high", "anger"): "critical",
        ("high", "negative"): "high",
        ("high", "neutral"): "high",
        ("high", "positive"): "medium",
        ("medium", "anger"): "high",
        ("medium", "negative"): "medium",
        ("medium", "neutral"): "medium",
        ("medium", "positive"): "low",
        ("low", "anger"): "medium",
        ("low", "negative"): "medium",
        ("low", "neutral"): "low",
        ("low", "positive"): "low",
        ("none", "anger"): "medium",
        ("none", "negative"): "low",
        ("none", "neutral"): "none",
        ("none", "positive"): "none",
    }
    return risk_matrix.get((harassment_severity, sentiment), "low")


def _ai_enhanced_analysis(message: str) -> dict | None:
    """
    Use Claude Opus 4.6 for nuanced harassment analysis.
    Returns structured analysis or None if unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            system=(
                "あなたはカスタマーハラスメント分析AIです。"
                "以下のメッセージを分析し、JSON形式で回答してください。"
                "キー: is_harassment (bool), severity (critical/high/medium/low/none), "
                "sentiment (anger/negative/neutral/positive), "
                "explanation (日本語で30文字以内の説明)"
            ),
            messages=[{"role": "user", "content": f"分析対象メッセージ: {message}"}],
        )
        result_text = response.content[0].text
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.warning("AI analysis failed: %s", e)

    return None


def lambda_handler(event, context):
    """
    Main Lambda handler for POST /api/analyze.

    Processes:
    1. Parse incoming message
    2. Run rule-based harassment detection
    3. Run rule-based sentiment analysis
    4. (Optional) AI-enhanced analysis for deeper context
    5. Calculate combined risk level
    6. Persist analytics to RDS
    7. Return analysis results
    """
    logger.info("Analyze function invoked")

    body = parse_body(event)
    if not body:
        return error_response("Request body is required", 400)

    message = body.get("message", "").strip()
    if not message:
        return error_response("Message is required", 400)

    conversation_id = body.get("conversation_id", "unknown")
    use_ai = body.get("use_ai", True)

    # Rule-based analysis
    harassment = detect_harassment(message)
    sentiment = analyze_sentiment(message)

    # AI-enhanced analysis (optional)
    ai_analysis = None
    if use_ai:
        ai_analysis = _ai_enhanced_analysis(message)

    # Combined risk
    combined_risk = _calculate_combined_risk(
        harassment.severity.value,
        sentiment.sentiment.value,
    )

    # Persist to database
    try:
        execute_insert(
            """
            INSERT INTO analysis_logs (
                conversation_id, message_text, harassment_severity,
                sentiment, combined_risk, ai_enhanced, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
            """,
            (
                conversation_id,
                message[:500],  # Truncate for storage
                harassment.severity.value,
                sentiment.sentiment.value,
                combined_risk,
                ai_analysis is not None,
            ),
        )
    except Exception as e:
        logger.error("Database write failed (non-blocking): %s", e)

    # Build response
    result = {
        "harassment": harassment.to_dict(),
        "sentiment": sentiment.to_dict(),
        "combined_risk": combined_risk,
        "ai_analysis": ai_analysis,
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    # Add alert flags
    if sentiment.trigger_alert:
        result["alert"] = {
            "type": "anger_detected",
            "message": "顧客の怒りを検出しました。即時対応を推奨します。",
            "severity": "high",
        }

    if harassment.is_harassment and harassment.severity.value in ("critical", "high"):
        result["alert"] = {
            "type": "harassment_detected",
            "message": f"カスハラ検出（{harassment.severity.value}）。{harassment.recommendation}",
            "severity": harassment.severity.value,
        }

    return success_response(result)
