"""
AI-to-Human handoff context builder.
Collects conversation metadata and summarizes context for human agents.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class HandoffContext:
    conversation_id: str
    customer_name: Optional[str]
    summary: str
    detected_issues: list[str]
    order_numbers: list[str]
    sentiment_history: list[str]
    harassment_detected: bool
    harassment_severity: Optional[str]
    priority: str  # critical, high, normal
    ai_resolution_attempted: bool
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "customer_name": self.customer_name,
            "summary": self.summary,
            "detected_issues": self.detected_issues,
            "order_numbers": self.order_numbers,
            "sentiment_history": self.sentiment_history,
            "harassment_detected": self.harassment_detected,
            "harassment_severity": self.harassment_severity,
            "priority": self.priority,
            "ai_resolution_attempted": self.ai_resolution_attempted,
            "metadata": self.metadata,
        }


def _extract_order_numbers(messages: list[dict]) -> list[str]:
    """Extract order numbers from conversation messages."""
    order_pattern = r"(?:注文番号|オーダー|order\s*(?:number|#|no\.?))\s*[：:]?\s*([A-Z0-9\-]+)"
    found = set()
    for msg in messages:
        text = msg.get("content", "")
        matches = re.findall(order_pattern, text, re.IGNORECASE)
        found.update(matches)
    return sorted(found)


def _extract_issues(messages: list[dict]) -> list[str]:
    """Extract detected issues from customer messages."""
    issue_patterns = {
        "配送問題": [r"届かない|届いていない|配送.*遅|配達.*来ない|発送.*まだ"],
        "品質問題": [r"壊れ|破損|不良|傷|汚れ|欠陥|故障|動かない"],
        "返品・返金": [r"返品|返金|キャンセル|取り消し|払い戻し"],
        "アカウント問題": [r"ログイン.*できない|パスワード|アカウント.*ロック"],
        "料金問題": [r"請求.*おかしい|二重.*課金|料金.*違う|値段.*間違"],
        "対応不満": [r"対応.*悪い|何度も.*問い合わせ|たらい回し|返事.*ない"],
    }
    issues = []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        text = msg.get("content", "")
        for issue_name, patterns in issue_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text) and issue_name not in issues:
                    issues.append(issue_name)
    return issues


def _determine_priority(
    harassment_detected: bool,
    harassment_severity: Optional[str],
    sentiment_history: list[str],
    message_count: int,
) -> str:
    """Determine handoff priority based on conversation context."""
    if harassment_detected and harassment_severity in ("critical", "high"):
        return "critical"
    if harassment_detected:
        return "high"
    anger_count = sentiment_history.count("anger")
    if anger_count >= 2:
        return "high"
    if anger_count >= 1 or message_count > 10:
        return "high"
    negative_count = sentiment_history.count("negative")
    if negative_count >= 3:
        return "high"
    return "normal"


def _generate_summary(messages: list[dict], issues: list[str]) -> str:
    """Generate a brief summary for the human agent."""
    customer_messages = [m for m in messages if m.get("role") == "user"]
    msg_count = len(customer_messages)

    if not customer_messages:
        return "顧客からのメッセージなし"

    first_msg = customer_messages[0].get("content", "")[:100]
    last_msg = customer_messages[-1].get("content", "")[:100] if msg_count > 1 else ""

    summary_parts = [f"顧客メッセージ数: {msg_count}"]

    if issues:
        summary_parts.append(f"検出された問題: {', '.join(issues)}")

    summary_parts.append(f"最初の問い合わせ: 「{first_msg}」")

    if last_msg:
        summary_parts.append(f"最新のメッセージ: 「{last_msg}」")

    return " | ".join(summary_parts)


def build_handoff_context(
    conversation_id: str,
    messages: list[dict],
    customer_name: Optional[str] = None,
    sentiment_history: Optional[list[str]] = None,
    harassment_detected: bool = False,
    harassment_severity: Optional[str] = None,
    ai_resolution_attempted: bool = True,
) -> HandoffContext:
    """
    Build handoff context for transferring conversation from AI to human agent.

    Args:
        conversation_id: Unique conversation identifier.
        messages: List of message dicts with {role, content, timestamp}.
        customer_name: Optional customer name.
        sentiment_history: List of sentiment labels over the conversation.
        harassment_detected: Whether harassment was detected.
        harassment_severity: Severity level if harassment detected.
        ai_resolution_attempted: Whether AI attempted to resolve the issue.

    Returns:
        HandoffContext with all collected metadata.
    """
    if sentiment_history is None:
        sentiment_history = []

    order_numbers = _extract_order_numbers(messages)
    issues = _extract_issues(messages)
    summary = _generate_summary(messages, issues)
    priority = _determine_priority(
        harassment_detected, harassment_severity, sentiment_history, len(messages)
    )

    return HandoffContext(
        conversation_id=conversation_id,
        customer_name=customer_name,
        summary=summary,
        detected_issues=issues,
        order_numbers=order_numbers,
        sentiment_history=sentiment_history,
        harassment_detected=harassment_detected,
        harassment_severity=harassment_severity,
        priority=priority,
        ai_resolution_attempted=ai_resolution_attempted,
        metadata={
            "total_messages": len(messages),
            "customer_messages": len([m for m in messages if m.get("role") == "user"]),
            "handoff_timestamp": datetime.utcnow().isoformat(),
        },
    )
