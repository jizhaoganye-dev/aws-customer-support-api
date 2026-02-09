"""
Sentiment analysis engine with anger detection.
Rule-based + AI-enhanced (Claude Opus 4.6 / Gemini 3).
Detects: positive, neutral, negative, anger — with confidence scores.
"""
import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGER = "anger"


@dataclass
class SentimentResult:
    sentiment: Sentiment
    confidence: float
    scores: dict[str, float]  # { positive: 0.1, neutral: 0.2, negative: 0.3, anger: 0.4 }
    trigger_alert: bool       # True if anger detected → dashboard alert
    keywords_found: list[str]

    def to_dict(self) -> dict:
        return {
            "sentiment": self.sentiment.value,
            "confidence": self.confidence,
            "scores": self.scores,
            "trigger_alert": self.trigger_alert,
            "keywords_found": self.keywords_found,
        }


# ── Keyword dictionaries ─────────────────────────────────────────────────────

POSITIVE_KEYWORDS = [
    "ありがとう", "助かり", "感謝", "嬉しい", "うれしい", "素晴らしい",
    "すばらしい", "最高", "完璧", "良い", "よい", "いい", "丁寧",
    "親切", "迅速", "便利", "満足", "解決", "サンキュー", "神対応",
    "great", "thanks", "thank you", "excellent", "good", "perfect",
]

NEGATIVE_KEYWORDS = [
    "不満", "不便", "残念", "がっかり", "困る", "困って", "心配",
    "不安", "面倒", "嫌", "いやだ", "ダメ", "だめ", "問題",
    "使えない", "分からない", "エラー", "バグ", "障害", "遅い",
    "改善", "苦情", "クレーム",
]

ANGER_KEYWORDS = [
    "怒り", "怒って", "激怒", "ふざけるな", "ふざけんな",
    "いい加減にしろ", "いい加減にして", "許さない", "許せない",
    "ありえない", "信じられない", "最悪", "最低", "酷い", "ひどい",
    "クソ", "くそ", "バカ", "ばか", "アホ", "死ね", "殺す",
    "キレ", "きれ", "ブチギレ", "ブチ切れ", "腹が立つ", "腹立つ",
    "むかつく", "ムカつく", "イライラ", "苛々", "頭にくる",
    "なめてる", "ナメてる", "舐めてる", "ゴミ", "カス",
]


def _count_matches(text: str, keywords: list[str]) -> tuple[int, list[str]]:
    """Count keyword matches and return (count, matched_keywords)."""
    found = []
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            found.append(kw)
    return len(found), found


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Analyze sentiment of the given text.

    Returns SentimentResult with scores for each sentiment category.
    Triggers alert if anger is detected (for dashboard notification).
    """
    if not text or not text.strip():
        return SentimentResult(
            sentiment=Sentiment.NEUTRAL,
            confidence=1.0,
            scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0, "anger": 0.0},
            trigger_alert=False,
            keywords_found=[],
        )

    pos_count, pos_found = _count_matches(text, POSITIVE_KEYWORDS)
    neg_count, neg_found = _count_matches(text, NEGATIVE_KEYWORDS)
    ang_count, ang_found = _count_matches(text, ANGER_KEYWORDS)

    total = pos_count + neg_count + ang_count + 1  # +1 for neutral base

    # Calculate raw scores
    pos_score = pos_count / total
    neg_score = neg_count / total
    ang_score = ang_count / total
    neu_score = 1 / total

    # Determine dominant sentiment
    all_found = pos_found + neg_found + ang_found

    if ang_count >= 2 or (ang_count >= 1 and neg_count >= 1):
        # Strong anger signal
        dominant = Sentiment.ANGER
        confidence = min(0.95, 0.6 + ang_count * 0.1)
    elif ang_count >= 1:
        dominant = Sentiment.ANGER
        confidence = 0.7
    elif neg_count > pos_count and neg_count >= 2:
        dominant = Sentiment.NEGATIVE
        confidence = min(0.9, 0.5 + neg_count * 0.1)
    elif neg_count > pos_count:
        dominant = Sentiment.NEGATIVE
        confidence = 0.6
    elif pos_count > neg_count and pos_count >= 2:
        dominant = Sentiment.POSITIVE
        confidence = min(0.9, 0.5 + pos_count * 0.1)
    elif pos_count > 0:
        dominant = Sentiment.POSITIVE
        confidence = 0.6
    else:
        dominant = Sentiment.NEUTRAL
        confidence = 0.8

    # Punctuation boosters (!! → more intense)
    exclamation_count = text.count("!") + text.count("！")
    if exclamation_count >= 3 and dominant in (Sentiment.NEGATIVE, Sentiment.ANGER):
        confidence = min(0.98, confidence + 0.1)
        ang_score += 0.1

    # Normalize scores
    score_total = pos_score + neg_score + ang_score + neu_score
    if score_total > 0:
        scores = {
            "positive": round(pos_score / score_total, 3),
            "neutral": round(neu_score / score_total, 3),
            "negative": round(neg_score / score_total, 3),
            "anger": round(ang_score / score_total, 3),
        }
    else:
        scores = {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "anger": 0.0}

    trigger_alert = dominant == Sentiment.ANGER

    return SentimentResult(
        sentiment=dominant,
        confidence=round(confidence, 3),
        scores=scores,
        trigger_alert=trigger_alert,
        keywords_found=all_found,
    )
