"""
Chat Lambda Function — AI Customer Support Chat API.
POST /api/chat

Accepts: { "message": "...", "conversation_id": "...", "customer_name": "..." }
Returns: { "response": "...", "sentiment": {...}, "harassment": {...}, "handoff": null|{...} }

Uses Claude Opus 4.6 API when ANTHROPIC_API_KEY is set,
falls back to comprehensive rule-based response engine.
"""
import json
import os
import uuid
import logging
from datetime import datetime

from response_helpers import success_response, error_response, parse_body
from harassment_detector import detect_harassment
from sentiment_analyzer import analyze_sentiment, Sentiment
from handoff import build_handoff_context
from db import execute_insert, execute_query

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ── Rule-based AI response engine ─────────────────────────────────────────────

RESPONSE_RULES: list[tuple[list[str], str]] = [
    # Shipping issues
    (
        ["届かない", "届いていない", "配送", "配達", "発送", "shipping"],
        "ご注文の配送状況を確認いたします。注文番号をお教えいただけますか？"
        "通常、出荷後2〜5営業日でのお届けとなります。"
        "追跡番号をお持ちの場合はそちらもお知らせください。",
    ),
    # Return / Refund
    (
        ["返品", "返金", "キャンセル", "取り消し", "払い戻し", "return", "refund"],
        "返品・返金のご希望を承ります。ご注文日から30日以内の商品であれば、"
        "未使用品に限り全額返金いたします。注文番号と返品理由をお知らせください。",
    ),
    # Product defect
    (
        ["壊れ", "不良", "破損", "故障", "動かない", "傷", "defect", "broken"],
        "商品の不具合について、大変申し訳ございません。"
        "お手数ですが、不具合の状態がわかるお写真をお送りいただけますか？"
        "確認後、交換または返金にて対応いたします。",
    ),
    # Account issues
    (
        ["ログイン", "パスワード", "アカウント", "login", "password", "account"],
        "アカウントに関するお問い合わせですね。"
        "パスワードリセットはログイン画面の「パスワードを忘れた方」から行えます。"
        "それでも解決しない場合は、ご登録のメールアドレスをお知らせください。",
    ),
    # Billing
    (
        ["請求", "課金", "料金", "支払い", "billing", "charge", "payment"],
        "お支払いに関するお問い合わせを承ります。"
        "請求内容の詳細を確認いたしますので、対象の注文番号または請求日をお知らせください。",
    ),
    # Greeting
    (
        ["こんにちは", "はじめまして", "よろしく", "hello", "hi"],
        "こんにちは！カスタマーサポートへようこそ。"
        "お問い合わせ内容をお聞かせください。何でもお気軽にどうぞ。",
    ),
    # Thanks
    (
        ["ありがとう", "感謝", "助かり", "thank"],
        "お役に立てて嬉しいです！他にお困りのことがあればいつでもお声がけください。",
    ),
]

DEFAULT_RESPONSE = (
    "お問い合わせありがとうございます。ご質問の内容を確認させていただきます。"
    "もう少し詳しくお聞かせいただけますか？"
    "具体的な注文番号やサービス名をお知らせいただけるとスムーズにご対応できます。"
)


def _generate_rule_based_response(message: str) -> str:
    """Generate a response using rule-based pattern matching."""
    message_lower = message.lower()
    for keywords, response in RESPONSE_RULES:
        if any(kw in message_lower for kw in keywords):
            return response
    return DEFAULT_RESPONSE


def _generate_ai_response(message: str, conversation_history: list[dict]) -> str:
    """Generate a response using Claude Opus 4.6 API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _generate_rule_based_response(message)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = (
            "あなたはカスタマーサポートAIアシスタントです。"
            "日本語で丁寧に、かつ迅速に対応してください。"
            "カスタマーハラスメントには冷静に対応し、必要に応じて上席者への引き継ぎを提案してください。"
            "回答は簡潔かつ具体的にしてください（200文字以内推奨）。"
        )

        messages = []
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        messages.append({"role": "user", "content": message})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    except Exception as e:
        logger.warning("Claude API call failed, falling back to rule-based: %s", e)
        return _generate_rule_based_response(message)


# ── Lambda Handler ────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    """
    Main Lambda handler for POST /api/chat.

    Processes:
    1. Parse incoming message
    2. Detect harassment
    3. Analyze sentiment
    4. Generate AI response (Claude or rule-based)
    5. Check if handoff needed
    6. Persist to RDS
    7. Return response
    """
    logger.info("Chat function invoked")

    # Parse request body
    body = parse_body(event)
    if not body:
        return error_response("Request body is required", 400)

    message = body.get("message", "").strip()
    if not message:
        return error_response("Message is required", 400)

    conversation_id = body.get("conversation_id", str(uuid.uuid4()))
    customer_name = body.get("customer_name")
    history = body.get("history", [])

    # Step 1: Harassment detection
    harassment = detect_harassment(message)
    logger.info("Harassment: %s (severity=%s)", harassment.is_harassment, harassment.severity.value)

    # Step 2: Sentiment analysis
    sentiment = analyze_sentiment(message)
    logger.info("Sentiment: %s (confidence=%.2f, alert=%s)", sentiment.sentiment.value, sentiment.confidence, sentiment.trigger_alert)

    # Step 3: Generate AI response
    if harassment.is_harassment and harassment.severity.value in ("critical", "high"):
        ai_response = (
            "お気持ちは理解いたします。"
            "適切にお答えするため、担当者にお繋ぎいたします。少々お待ちください。"
        )
        needs_handoff = True
    else:
        ai_response = _generate_ai_response(message, history)
        needs_handoff = False

    # Step 4: Build handoff context if needed
    handoff_context = None
    if needs_handoff or sentiment.trigger_alert:
        handoff = build_handoff_context(
            conversation_id=conversation_id,
            messages=history + [{"role": "user", "content": message}],
            customer_name=customer_name,
            sentiment_history=[sentiment.sentiment.value],
            harassment_detected=harassment.is_harassment,
            harassment_severity=harassment.severity.value,
        )
        handoff_context = handoff.to_dict()

    # Step 5: Persist to database
    try:
        # Save user message
        execute_insert(
            """
            INSERT INTO messages (conversation_id, role, content, sentiment, harassment_severity, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
            """,
            (conversation_id, "user", message, sentiment.sentiment.value, harassment.severity.value),
        )

        # Save AI response
        execute_insert(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
            """,
            (conversation_id, "assistant", ai_response),
        )

        # Log harassment event if detected
        if harassment.is_harassment:
            execute_insert(
                """
                INSERT INTO harassment_events (conversation_id, severity, categories, matched_patterns, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (
                    conversation_id,
                    harassment.severity.value,
                    json.dumps(harassment.categories),
                    json.dumps(harassment.matched_patterns),
                ),
            )

    except Exception as e:
        logger.error("Database write failed (non-blocking): %s", e)

    # Step 6: Return response
    return success_response({
        "conversation_id": conversation_id,
        "response": ai_response,
        "sentiment": sentiment.to_dict(),
        "harassment": harassment.to_dict(),
        "handoff": handoff_context,
        "needs_handoff": needs_handoff,
        "timestamp": datetime.utcnow().isoformat(),
    })
